-- One row per product event.
select
    event_id,
    user_id,
    cast(event_ts as timestamp)     as event_ts,
    event_name,
    cast(characters as integer)     as characters
from read_csv_auto('{{ var("raw_path") }}/events.csv', header = true)
