-- One row per user in the onboarding_v2 experiment, with every metric the
-- experiment readout needs. The analysis notebook reads only this table.
select
    user_id,
    variant,
    signup_ts,
    country,
    channel,
    device,
    pre_signup_sessions,   -- CUPED covariate: measured before assignment
    is_activated_7d,       -- primary metric
    voices_28d,
    characters_28d,        -- secondary metric
    is_week_4_observed,
    is_active_week_4,      -- secondary metric
    is_paid_28d            -- guardrail metric
from {{ ref('dim_users') }}
where experiment_id = 'onboarding_v2'
