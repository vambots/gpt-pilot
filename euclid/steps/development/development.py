import json
from termcolor import colored

from utils.utils import execute_step, find_role_from_step, generate_app_data
from database.database import save_progress, get_progress_steps
from logger.logger import logger
from prompts.prompts import get_additional_info_from_user, execute_chat_prompt
from const.function_calls import FILTER_OS_TECHNOLOGIES, COMMANDS_TO_RUN
from const.code_execution import MAX_COMMAND_DEBUG_TRIES
from utils.utils import get_os_info
from helpers.cli import execute_command

def environment_setup():
    # env_setup/specs.prompt
    # loop through returned array
        # install_next_technology.prompt
            # cli_response.prompt
            # unsuccessful_installation.prompt

            # OR
            execute_command();

def implement_task(task):
    # development/task/breakdown.prompt
    # loop through returned array
        # development/task/step/specs.prompt
        
    pass

def install_technology(technology):
      pass

def execute_command_and_check_cli_response(command, timeout, previous_messages, current_step):
    cli_response = execute_command(command, timeout)
    response, messages = execute_chat_prompt('dev_ops/ran_command.prompt',
        { 'cli_response': cli_response, 'command': command }, current_step, previous_messages)
    return response, messages

def run_command_until_success(command, timeout, previous_messages, current_step):
    command_executed = False
    for _ in range(MAX_COMMAND_DEBUG_TRIES):
        cli_response = execute_command(command, timeout)
        response, previous_messages = execute_chat_prompt('dev_ops/ran_command.prompt',
            {'cli_response': cli_response, 'command': command}, current_step, previous_messages)
        
        command_executed = response == 'DONE'
        if command_executed:
            break

        command = response

    if not command_executed:
        # TODO ask user to debug and press enter to continue
        pass

def set_up_environment(technologies, args):
    current_step = 'environment_setup'
    role = find_role_from_step(current_step)

    steps = get_progress_steps(args['app_id'], current_step)
    if steps and not execute_step(args['step'], current_step):
        first_step = steps[0]
        data = json.loads(first_step['data'])

        app_data = data.get('app_data')
        if app_data is not None:
            args.update(app_data)

        message = f"Tech stask breakdown already done for this app_id: {args['app_id']}. Moving to next step..."
        print(colored(message, "green"))
        logger.info(message)
        return data.get('technologies'), data.get('messages')
    
    # ENVIRONMENT SETUP
    print(colored(f"Setting up the environment...\n", "green"))
    logger.info(f"Setting up the environment...")

    # TODO: remove this once the database is set up properly
    # previous_messages[2]['content'] = '\n'.join(previous_messages[2]['content'])
    # TODO END

    os_info = get_os_info()
    # os_specific_techologies, previous_messages = execute_chat_prompt('development/env_setup/specs.prompt',
    #         { "os_info": os_info, "technologies": technologies }, current_step, function_calls=FILTER_OS_TECHNOLOGIES)
    
    os_specific_techologies = ['Heroku']
    previous_messages = [{'role': 'system', 'content': ''}, {'role': 'user', 'content': "You are working in a software development agency and a project manager and software architect approach you telling you that you're assigned to work on a new project. You are working on a web app called Euclid and your first job is to set up the environment on a computer.\n\nHere are the technologies that you need to use for this project:\n```\n\n- 1. Node.js\n\n- 2. Express.js\n\n- 3. Axios\n\n- 4. Github API\n\n- 5. Jest\n\n- 6. D3.js\n\n- 7. Tailwind\n\n- 8. HTML\n\n- 9. Vanilla Javascript\n\n- 10. Cypress\n\n- 11. API Bakery\n\n- 12. Heroku or similar web hosting service for Node.js apps\n\n- 13. Git & Github for version control.\n\n```\n\nLet's set up the environment on my machine. Here are the details about my machine:\n```\nOS: Darwin\nOS Version: Darwin Kernel Version 22.5.0: Mon Apr 24 20:53:19 PDT 2023; root:xnu-8796.121.2~5/RELEASE_ARM64_T6020\nArchitecture: 64bit\nMachine: arm64\nNode: Zvonimirs-MacBook-Pro.local\nRelease: 22.5.0\n```\n\nFirst, filter out the technologies from the list above and tell me, which technologies need to be installed on my machine. That is everything OS specific and not dependencies, libraries, etc. Do not respond with anything else except the list in a JSON array format."}, {'role': 'assistant', 'content': ['Node.js', 'Git & Github for version control.', 'Heroku or similar web hosting service for Node.js apps']}]

    for technology in os_specific_techologies:
        llm_response, previous_messages = execute_chat_prompt('development/env_setup/install_next_technology.prompt',
            { 'technology': technology}, current_step, previous_messages, function_calls={
                'definitions': [{
                    'name': 'execute_command',
                    'description': f'Executes a command that should check if {technology} is installed on the machine. ',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'command': {
                                'type': 'string',
                                'description': f'Command that needs to be executed to check if {technology} is installed on the machine.',
                            },
                            'timeout': {
                                'type': 'number',
                                'description': f'Timeout in seconds for the approcimate time this command takes to finish.',
                            }
                        },
                        'required': ['command', 'timeout'],
                    },
                }],
                'functions': {
                    'execute_command': execute_command_and_check_cli_response
                },
                'send_messages_and_step': True
            })
        
        if not llm_response == 'DONE':
            installation_commands, previous_messages = execute_chat_prompt('development/env_setup/unsuccessful_installation.prompt',
                { 'technology': technology }, current_step, previous_messages, function_calls={
                'definitions': [{
                    'name': 'execute_commands',
                    'description': f'Executes a list of commands that should install the {technology} on the machine. ',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'commands': {
                                 'type': 'array',
                                 'description': f'List of commands that need to be executed to install {technology} on the machine.',
                                 'items': {
                                    'type': 'object',
                                    'properties': {
                                         'command': {
                                            'type': 'string',
                                            'description': f'Command that needs to be executed as a step to install {technology} on the machine.',
                                        },
                                        'timeout': {
                                            'type': 'number',
                                            'description': f'Timeout in seconds for the approcimate time this command takes to finish.',
                                        }
                                    }
                                }
                            }
                        },
                        'required': ['commands'],
                    },
                }],
                'functions': {
                    'execute_commands': lambda commands: (commands, None)
                }
            })
            if installation_commands is not None:
                for cmd in installation_commands:
                    run_command_until_success(cmd['command'], cmd['timeout'], previous_messages, current_step)
        



    logger.info('The entire tech stack neede is installed and ready to be used.')

    # TODO save conversations to database
    # save_progress(args['app_id'], current_step, {
    #     "messages": user_tasks_messages,"user_tasks": user_tasks, "app_data": generate_app_data(args)
    # })

    # ENVIRONMENT SETUP END



    for technology in technologies:
          install_technology(technology)

def start_development(user_stories, user_tasks, technologies_to_use, args):
    # break down the development plan
    # set up the environment
    # TODO REMOVE THIS
    technologies_to_use = technologies_to_use.split('\n')
    # TODO END
    set_up_environment(technologies_to_use, args);
    pass