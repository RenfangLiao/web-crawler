redis-server &
export FLASK_APP='web_crawler:application'
flask run --host=0.0.0.0 -p 8080
