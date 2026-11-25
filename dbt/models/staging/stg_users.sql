-- One row per user, with clean types.
select
    user_id,
    cast(signup_ts as timestamp)            as signup_ts,
    cast(signup_ts as date)                 as signup_date,
    cast(date_trunc('week', cast(signup_ts as timestamp)) as date) as signup_week,
    country,
    channel,
    device,
    cast(pre_signup_sessions as integer)    as pre_signup_sessions
from read_csv_auto('{{ var("raw_path") }}/users.csv', header = true)
