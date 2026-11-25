-- One row per user: when they first reached each step of the funnel.
select
    user_id,
    min(case when event_name = 'project_created'      then event_ts end) as first_project_ts,
    min(case when event_name = 'voice_generated'      then event_ts end) as first_voice_ts,
    min(case when event_name = 'subscription_started' then event_ts end) as first_subscription_ts
from {{ ref('stg_events') }}
group by user_id
