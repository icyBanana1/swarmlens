from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

from .utils import bucket_time, clamp, grade, jaccard_similarity, normalize_text, parse_bool, parse_datetime, safe_int, tokenize


def analyze_case(data: dict[str, list[dict[str, Any]]], case_name: str = "case") -> dict[str, Any]:
    accounts_rows = data.get("accounts", [])
    posts_rows = data.get("posts", [])
    interactions_rows = data.get("interactions", [])
    now = datetime.now(timezone.utc)

    posts_by_account: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interactions_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interactions_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for post in posts_rows:
        posts_by_account[str(post.get("account_id", "")).strip()].append(post)
    for interaction in interactions_rows:
        s = str(interaction.get("source_account_id", "")).strip()
        t = str(interaction.get("target_account_id", "")).strip()
        interactions_by_source[s].append(interaction)
        interactions_by_target[t].append(interaction)

    duplicate_bios = Counter(normalize_text(str(r.get("bio", ""))) for r in accounts_rows if normalize_text(str(r.get("bio", ""))))
    duplicate_names = Counter(str(r.get("username", "")).strip().lower() for r in accounts_rows if str(r.get("username", "")).strip())

    account_scores: dict[str, dict[str, Any]] = {}
    account_summary_rows: list[dict[str, Any]] = []
    for row in accounts_rows:
        aid = str(row.get("account_id", "")).strip()
        username = str(row.get("username", aid)).strip() or aid
        reasons: list[str] = []
        evidence: list[dict[str, Any]] = []
        score = 0.0

        created_at = parse_datetime(row.get("created_at"))
        age_days = None
        if created_at:
            age_days = max((now - created_at.astimezone(timezone.utc)).days, 0)
            if age_days < 30:
                score += 0.15; reasons.append("new-account"); evidence.append({"rule": "new-account", "weight": 0.15, "detail": f"age_days={age_days}"})
            elif age_days < 120:
                score += 0.07; reasons.append("recent-account")

        followers = safe_int(row.get("followers_count"))
        following = safe_int(row.get("following_count"))
        posts_count = safe_int(row.get("posts_count"))
        ff_ratio = followers / max(following, 1)
        if following > 200 and ff_ratio < 0.2:
            score += 0.12; reasons.append("follower-following-imbalance"); evidence.append({"rule": "ratio", "weight": 0.12, "detail": f"followers={followers}, following={following}"})
        if parse_bool(row.get("profile_image_default")):
            score += 0.08; reasons.append("default-profile-image")
        if not parse_bool(row.get("verified")) and followers < 50 and posts_count > 450:
            score += 0.14; reasons.append("high-post-volume-low-trust")
        bio_norm = normalize_text(str(row.get("bio", "")))
        if bio_norm and duplicate_bios[bio_norm] >= 3:
            score += 0.10; reasons.append("duplicate-bio-pattern")
        uname_norm = username.lower()
        if duplicate_names[uname_norm] > 1:
            score += 0.05; reasons.append("duplicate-display-pattern")

        account_posts = sorted(posts_by_account.get(aid, []), key=lambda p: parse_datetime(p.get("timestamp")) or now)
        timestamps = [parse_datetime(p.get("timestamp")) for p in account_posts if parse_datetime(p.get("timestamp"))]
        if len(timestamps) >= 4:
            span_hours = max((timestamps[-1] - timestamps[0]).total_seconds() / 3600.0, 0.1)
            pph = len(timestamps) / span_hours
            if pph > 18:
                score += 0.17; reasons.append("posting-burst-pattern")
            elif pph > 9:
                score += 0.09; reasons.append("high-posting-intensity")
        if account_posts:
            texts = [normalize_text(str(p.get("text", ""))) for p in account_posts if str(p.get("text", "")).strip()]
            reused_self = 1 - len(set(texts)) / max(len(texts), 1)
            if reused_self >= 0.35 and len(texts) >= 5:
                score += 0.11; reasons.append("self-text-repetition"); evidence.append({"rule": "self-text-repetition", "weight": 0.11, "detail": f"repeat_ratio={reused_self:.2f}"})

        out_interactions = interactions_by_source.get(aid, [])
        in_interactions = interactions_by_target.get(aid, [])
        if len(out_interactions) > 12 and len({str(x.get('target_account_id','')).strip() for x in out_interactions}) <= 3:
            score += 0.12; reasons.append("narrow-target-amplification")
        if len(in_interactions) >= 8:
            suspicious_sources = 0
            for x in in_interactions:
                source = str(x.get("source_account_id", "")).strip()
                if account_scores.get(source, {}).get("score", 0) >= 0.45:
                    suspicious_sources += 1
            if suspicious_sources >= 5:
                score += 0.06; reasons.append("boosted-by-suspicious-accounts")

        score = clamp(score)
        account_scores[aid] = {
            "account_id": aid,
            "username": username,
            "platform": str(row.get("platform", "unknown")),
            "score": round(score, 4),
            "grade": grade(score),
            "reasons": sorted(set(reasons)),
            "evidence": evidence,
            "metrics": {
                "age_days": age_days,
                "followers": followers,
                "following": following,
                "posts": posts_count,
                "post_events": len(account_posts),
                "incoming_interactions": len(in_interactions),
                "outgoing_interactions": len(out_interactions),
            },
        }
        account_summary_rows.append(account_scores[aid])

    # Text and phrase reuse
    normalized_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hashtag_counter: Counter[str] = Counter()
    for row in posts_rows:
        text_norm = normalize_text(str(row.get("text", "")))
        if text_norm:
            normalized_groups[text_norm].append(row)
        for h in str(row.get("hashtags", "")).split(","):
            h = h.strip().lower().lstrip("#")
            if h:
                hashtag_counter[h] += 1

    exact_reuse = []
    for text, group in normalized_groups.items():
        accounts = sorted({str(p.get("account_id", "")) for p in group})
        if len(accounts) >= 2:
            exact_reuse.append({
                "text": text[:220],
                "count": len(group),
                "accounts": accounts,
                "unique_accounts": len(accounts),
                "post_ids": [str(p.get("post_id", "")) for p in group[:30]],
            })
    exact_reuse.sort(key=lambda x: (x["unique_accounts"], x["count"]), reverse=True)

    sample_posts = [p for p in posts_rows if str(p.get("text", "")).strip()][:250]
    near_duplicates = []
    for a, b in combinations(sample_posts, 2):
        if str(a.get("account_id", "")) == str(b.get("account_id", "")):
            continue
        sim = jaccard_similarity(tokenize(str(a.get("text", ""))), tokenize(str(b.get("text", ""))))
        if sim >= 0.72:
            near_duplicates.append({
                "post_a": str(a.get("post_id", "")),
                "post_b": str(b.get("post_id", "")),
                "account_a": str(a.get("account_id", "")),
                "account_b": str(b.get("account_id", "")),
                "similarity": round(sim, 3),
                "preview": normalize_text(str(a.get("text", "")))[:180],
            })
    near_duplicates.sort(key=lambda x: x["similarity"], reverse=True)

    # Temporal bursts and coordination
    bursts_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sync_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    timeline_counter: Counter[str] = Counter()
    for row in posts_rows:
        dt = parse_datetime(row.get("timestamp"))
        bucket = bucket_time(dt, 120)
        bursts_map[bucket].append(row)
        timeline_counter[bucket] += 1
        phrase = normalize_text(str(row.get("text", "")))
        if phrase:
            sync_map[(bucket, phrase)].append(row)
    bursts = []
    for bucket, rows in bursts_map.items():
        accounts = sorted({str(r.get("account_id", "")) for r in rows})
        if len(accounts) >= 3:
            bursts.append({"bucket": bucket, "post_count": len(rows), "unique_accounts": len(accounts), "accounts": accounts[:25]})
    bursts.sort(key=lambda x: (x["unique_accounts"], x["post_count"]), reverse=True)

    synchronized_messages = []
    for (bucket, phrase), rows in sync_map.items():
        accounts = sorted({str(r.get("account_id", "")) for r in rows})
        if len(accounts) >= 3:
            synchronized_messages.append({
                "bucket": bucket,
                "phrase": phrase[:220],
                "post_count": len(rows),
                "unique_accounts": len(accounts),
                "accounts": accounts[:25],
            })
    synchronized_messages.sort(key=lambda x: (x["unique_accounts"], x["post_count"]), reverse=True)

    # Network analysis
    adjacency: dict[str, set[str]] = defaultdict(set)
    edge_counts: Counter[tuple[str, str]] = Counter()
    interaction_type_counter: Counter[str] = Counter()
    for row in interactions_rows:
        s = str(row.get("source_account_id", "")).strip()
        t = str(row.get("target_account_id", "")).strip()
        kind = str(row.get("interaction_type", "unknown")).strip().lower() or "unknown"
        if not s or not t or s == t:
            continue
        adjacency[s].add(t)
        adjacency[t].add(s)
        edge_counts[(s, t)] += 1
        interaction_type_counter[kind] += 1

    visited: set[str] = set()
    components: list[list[str]] = []
    for node in adjacency:
        if node in visited:
            continue
        q = deque([node])
        visited.add(node)
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nb in adjacency[cur]:
                if nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        if len(comp) >= 3:
            components.append(sorted(comp))
    components.sort(key=len, reverse=True)

    central_accounts = []
    for node, neighbors in adjacency.items():
        centrality = len(neighbors) + sum(edge_counts.get((node, nb), 0) + edge_counts.get((nb, node), 0) for nb in neighbors) * 0.15
        central_accounts.append({
            "account_id": node,
            "username": account_scores.get(node, {}).get("username", node),
            "neighbors": len(neighbors),
            "centrality_score": round(centrality, 3),
            "risk_score": account_scores.get(node, {}).get("score", 0),
        })
    central_accounts.sort(key=lambda x: x["centrality_score"], reverse=True)

    suspicious_pairs = []
    for (a, b), count in edge_counts.items():
        if count >= 2:
            pair_score = count * 0.2 + account_scores.get(a, {}).get("score", 0) * 0.3 + account_scores.get(b, {}).get("score", 0) * 0.3
            suspicious_pairs.append({
                "source": a,
                "target": b,
                "count": count,
                "pair_score": round(min(pair_score, 1.0), 3),
            })
    suspicious_pairs.sort(key=lambda x: x["pair_score"], reverse=True)

    # Engagement authenticity by target
    authenticity = []
    for target, inbound in interactions_by_target.items():
        total = len(inbound)
        if total == 0:
            continue
        suspicious_weight = 0.0
        unique_sources = set()
        for x in inbound:
            source = str(x.get("source_account_id", "")).strip()
            unique_sources.add(source)
            suspicious_weight += account_scores.get(source, {}).get("score", 0)
        suspicious_ratio = suspicious_weight / max(total, 1)
        authenticity_score = clamp(1.0 - suspicious_ratio * 0.75 - (1.0 - len(unique_sources)/max(total,1))*0.25)
        authenticity.append({
            "target_account_id": target,
            "target_username": account_scores.get(target, {}).get("username", target),
            "authenticity_score": round(authenticity_score, 3),
            "suspicious_support": round(suspicious_ratio, 3),
            "interaction_count": total,
            "unique_sources": len(unique_sources),
        })
    authenticity.sort(key=lambda x: x["authenticity_score"])

    # Cluster summaries
    cluster_summaries = []
    nodes = set(adjacency)
    for idx, comp in enumerate(components, start=1):
        cluster_posts = [p for p in posts_rows if str(p.get("account_id", "")).strip() in comp]
        cluster_phrases = Counter(normalize_text(str(p.get("text", ""))) for p in cluster_posts if str(p.get("text", "")).strip())
        top_phrase, top_count = ("", 0)
        if cluster_phrases:
            top_phrase, top_count = cluster_phrases.most_common(1)[0]
        avg_risk = sum(account_scores.get(node, {}).get("score", 0.0) for node in comp) / max(len(comp), 1)
        cluster_summaries.append({
            "cluster_id": f"cluster-{idx}",
            "size": len(comp),
            "accounts": comp,
            "average_risk": round(avg_risk, 3),
            "top_phrase": top_phrase[:160],
            "top_phrase_count": top_count,
            "grade": grade(avg_risk),
        })
    cluster_summaries.sort(key=lambda x: (x["average_risk"], x["size"]), reverse=True)

    # Composite campaign score
    campaign_score = 0.0
    campaign_score += min(len([a for a in account_scores.values() if a["score"] >= 0.65]) / max(len(account_scores), 1), 1.0) * 0.32
    campaign_score += min(len(cluster_summaries) / 5, 1.0) * 0.16
    campaign_score += min((synchronized_messages[0]["unique_accounts"] / 12), 1.0) * 0.20 if synchronized_messages else 0
    campaign_score += min((exact_reuse[0]["unique_accounts"] / 12), 1.0) * 0.18 if exact_reuse else 0
    campaign_score += min((bursts[0]["unique_accounts"] / 12), 1.0) * 0.14 if bursts else 0
    campaign_score = clamp(campaign_score)

    summary = {
        "case_name": case_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accounts": len(accounts_rows),
        "posts": len(posts_rows),
        "interactions": len(interactions_rows),
        "high_risk_accounts": sum(1 for x in account_scores.values() if x["score"] >= 0.65),
        "coordinated_clusters": len(cluster_summaries),
        "campaign_score": round(campaign_score, 3),
        "campaign_grade": grade(campaign_score),
        "top_hashtags": [{"tag": tag, "count": count} for tag, count in hashtag_counter.most_common(10)],
    }

    graph = {
        "nodes": [{"id": aid, "label": info["username"], "risk": info["score"], "grade": info["grade"]} for aid, info in account_scores.items()],
        "edges": [{"source": a, "target": b, "count": count} for (a, b), count in edge_counts.items()],
    }

    return {
        "summary": summary,
        "account_scores": sorted(account_summary_rows, key=lambda x: x["score"], reverse=True),
        "exact_reuse": exact_reuse[:50],
        "near_duplicates": near_duplicates[:80],
        "bursts": bursts[:50],
        "synchronized_messages": synchronized_messages[:50],
        "central_accounts": central_accounts[:50],
        "suspicious_pairs": suspicious_pairs[:80],
        "authenticity": authenticity[:50],
        "cluster_summaries": cluster_summaries[:30],
        "timeline": [{"bucket": bucket, "post_count": count} for bucket, count in sorted(timeline_counter.items())],
        "interaction_types": dict(interaction_type_counter),
        "graph": graph,
    }


def explain_account(report: dict[str, Any], account_id: str) -> dict[str, Any] | None:
    for account in report.get("account_scores", []):
        if str(account.get("account_id")) == str(account_id):
            cluster_matches = [c for c in report.get("cluster_summaries", []) if account_id in c.get("accounts", [])]
            pair_matches = [p for p in report.get("suspicious_pairs", []) if account_id in {p.get("source"), p.get("target")}][:10]
            return {
                "account": account,
                "clusters": cluster_matches,
                "suspicious_pairs": pair_matches,
            }
    return None
