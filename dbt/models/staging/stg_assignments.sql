-- One row per user in an experiment.
select
    user_id,
    experiment_id,
    variant,
    cast(assigned_ts as timestamp)  as assigned_ts
from read_csv_auto('{{ var("raw_path") }}/assignments.csv', header = true)
