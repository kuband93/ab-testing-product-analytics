-- One row per user with the certified user-level product metrics.
-- Every metric is defined here once and reused by every analysis.
{% set data_end = "timestamp '" ~ var('data_end') ~ "'" %}

with usage_28d as (
    select
        e.user_id,
        count(*)          as voices_28d,
        sum(e.characters) as characters_28d
    from {{ ref('stg_events') }} as e
    join {{ ref('stg_users') }}  as u using (user_id)
    where e.event_name = 'voice_generated'
      and e.event_ts < u.signup_ts + interval 28 day
    group by 1
),

week_4 as (
    select user_id, true as active_week_4
    from {{ ref('int_user_weekly_activity') }}
    where week_number = 4
)

select
    u.user_id,
    u.signup_ts,
    u.signup_date,
    u.signup_week,
    u.country,
    u.channel,
    u.device,
    u.pre_signup_sessions,

    -- experiment
    a.experiment_id,
    a.variant,

    -- funnel milestones
    m.first_project_ts,
    m.first_voice_ts,
    m.first_subscription_ts,

    -- ACTIVATION: first voice generated within 7 days of sign-up
    coalesce(m.first_voice_ts < u.signup_ts + interval 7 day, false)         as is_activated_7d,

    -- USAGE: voices and characters generated in the first 28 days
    coalesce(g.voices_28d, 0)                                                as voices_28d,
    coalesce(g.characters_28d, 0)                                            as characters_28d,

    -- PAID CONVERSION (guardrail): subscription started within 28 days
    coalesce(m.first_subscription_ts < u.signup_ts + interval 28 day, false) as is_paid_28d,

    -- RETENTION: active in week 4 (days 28-34). Only defined when the whole
    -- week has been observed; otherwise null, so averages stay unbiased.
    u.signup_ts + interval 35 day <= {{ data_end }}                          as is_week_4_observed,
    case
        when u.signup_ts + interval 35 day <= {{ data_end }}
        then coalesce(w.active_week_4, false)
    end                                                                      as is_active_week_4

from {{ ref('stg_users') }}                as u
left join {{ ref('stg_assignments') }}     as a using (user_id)
left join {{ ref('int_user_milestones') }} as m using (user_id)
left join usage_28d                        as g using (user_id)
left join week_4                           as w using (user_id)
