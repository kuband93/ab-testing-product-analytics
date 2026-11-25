-- Sample-ratio check: with a 50/50 design, neither variant should hold
-- less than 48% of users. Fails loudly if assignment is broken.
select variant, count(*) * 1.0 / sum(count(*)) over () as share
from {{ ref('fct_experiment_users') }}
group by variant
qualify share < 0.48
