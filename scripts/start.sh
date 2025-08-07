#!/bin/bash
# Start Nova Corpus Pipeline

echo "🚀 Starting Nova Corpus Pipeline..."

# Check environment
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example and configure."
    exit 1
fi

# Load environment
source .env

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Start ingestion engine
echo "Starting ingestion engine..."
nohup python -m pipeline.ingestion.engine > logs/ingestion.log 2>&1 &
echo $! > logs/ingestion.pid

# Start monitoring dashboard
echo "Starting monitoring dashboard..."
nohup python -m pipeline.monitoring.dashboard > logs/dashboard.log 2>&1 &
echo $! > logs/dashboard.pid

# Start Airflow if configured
if [ "$USE_AIRFLOW" = "true" ]; then
    echo "Starting Airflow..."
    airflow db init
    nohup airflow scheduler > logs/airflow-scheduler.log 2>&1 &
    nohup airflow webserver -p 8080 > logs/airflow-webserver.log 2>&1 &
fi

echo "✅ Pipeline started successfully!"
echo ""
echo "📊 Monitoring dashboard: http://localhost:5000"
echo "📁 Logs directory: ./logs/"
echo ""
echo "To stop: ./scripts/stop.sh"