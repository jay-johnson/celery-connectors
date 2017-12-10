broker_url = 'amqp://rabbitmq:rabbitmq@localhost:5672//'
result_backend = 'rpc://'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'America/Los_Angeles'

task_routes = {'run.check_values': 'low-priority',
               'run.calculate_results': 'high-priority'}
