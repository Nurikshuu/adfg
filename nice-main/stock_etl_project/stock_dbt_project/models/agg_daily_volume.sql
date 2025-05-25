with daily as (
    select
        toDate(timestamp) as date,
        volume
    from {{ source('stock', 'daily_stock') }}
)

select
    date,
    sum(volume) as total_volume
from daily
group by date
order by date
