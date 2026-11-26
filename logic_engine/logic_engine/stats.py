"""Thống kê cho báo cáo."""


def collect_stats(kb):
    return {
        "primary_vars": kb.pool.num_primary,
        "aux_vars": kb.pool.num_aux,
        "clauses": len(kb.clauses),
    }
