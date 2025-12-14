import postgres from 'postgres'

const connectionString = "postgresql://postgres:[@HELLOWORLD2025]@db.ebfrasqlihxafmemcdrt.supabase.co:5432/postgres"
const sql = postgres(connectionString)
console.log(sql)
export default sql