-- Weekly retention by sign-up cohort: share of a cohort active N weeks after sign-up.
-- Cells where not every user in the cohort could be observed are left out.
{% set data_end = "timestamp '" ~ var('data_end') ~ "'" %}

with cohorts as (
    select signup_week, count(*) as cohort_size, max(signup_ts) as last_signup_ts
    from {{ ref('stg_users') }}
    group by 1
),

weeks as (
    select range as week_number from range(0, 12)
),

active as (
    select u.signup_week, a.week_number, count(distinct a.user_id) as active_users
    from {{ ref('int_user_weekly_activity') }} as a
    join {{ ref('stg_users') }}                as u using (user_id)
    group by 1, 2
)

select
    c.signup_week,
    w.week_number,
    c.cohort_size,
    coalesce(a.active_users, 0)                                  as active_users,
    coalesce(a.active_users, 0) * 1.0 / c.cohort_size            as retention_rate
from cohorts as c
cross join weeks as w
left join active as a
    on a.signup_week = c.signup_week and a.week_number = w.week_number
-- keep only weeks fully observed for the latest user in the cohort
where c.last_signup_ts + to_days(cast((w.week_number + 1) * 7 as integer)) <= {{ data_end }}
