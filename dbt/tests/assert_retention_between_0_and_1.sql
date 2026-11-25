-- Retention rates must be valid proportions.
select *
from {{ ref('fct_retention_cohorts') }}
where retention_rate < 0 or retention_rate > 1
