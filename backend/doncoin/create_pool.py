# Create a matching pool for testing
from base.models import MatchingPool

pool = MatchingPool.objects.create(
    total_funds=50000.00,
    allocated_funds=0.00,
    replenished_by="Community Treasury"
)

print(f"Created matching pool: {pool.pool_id}")
print(f"Total funds: ${pool.total_funds}")
