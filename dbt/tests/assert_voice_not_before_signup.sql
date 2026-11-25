-- A user cannot generate a voice before signing up. Returns offending rows.
select d.user_id
from {{ ref('dim_users') }} as d
where d.first_voice_ts < d.signup_ts
