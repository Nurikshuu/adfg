with daily as (
    select
        toYear(timestamp) as year,
        volume
    from {{ source('stock', 'daily_stock') }}
)

select
    year,
    avg(volume) as avg_volume
from daily
group by year
order by year
