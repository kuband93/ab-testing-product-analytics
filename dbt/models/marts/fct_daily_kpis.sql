-- Daily product KPIs by sign-up date: the numbers a product team checks every day.
select
    signup_date,
    count(*)                                  as signups,
    avg(case when is_activated_7d then 1.0 else 0.0 end) as activation_rate_7d,
    avg(case when is_paid_28d then 1.0 else 0.0 end)     as paid_rate_28d,
    avg(characters_28d)                       as avg_characters_28d
from {{ ref('dim_users') }}
group by 1
