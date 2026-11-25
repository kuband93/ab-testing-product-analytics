-- One row per user and week since sign-up in which the user was active.
-- Week 0 = the first 7 days after sign-up, week 1 = days 7-13, and so on.
-- "Active" = started a session or generated a voice.
select
    e.user_id,
    date_diff('second', u.signup_ts, e.event_ts) // (7 * 24 * 3600) as week_number,
    count(*)                                                          as active_events,
    sum(case when e.event_name = 'voice_generated' then 1 else 0 end) as voices
from {{ ref('stg_events') }} as e
join {{ ref('stg_users') }}  as u using (user_id)
where e.event_name in ('session_start', 'voice_generated')
group by 1, 2
