import os

from src.decoration.paint import paint
from src.utilities.get_utilities import GetUtilities


class ArgumentChecker:
    @staticmethod
    def check_arguments(command, arguments):
        """
        Check if the provided arguments are valid for the given command.

        Args:
            command (str): The command for which to check the arguments.
            arguments (list): The list of arguments provided by the user.

        Returns:
            bool: True if the arguments are valid, False if they are not.
        """

        commands = ArgumentChecker.get_command_indexes()

        if len(command) == 2:
            command = commands.get(command, command)

        if command in ['cls', 'clear', 'discord', 'exit', 'quit']:
            return True

        if command in ['language', 'server', 'uuid', 'ipinfo', 'dnslookup', 'websearch', 'listening', 'playerlogs', 'checker', 'waterfall', 'shodan']:
            if ArgumentChecker.missing_arguments(command, 1, arguments):
                return False
            
        if command in ['subdomains', 'fakeproxy', 'rconbrute', 'velocity', 'rcon']:
            if ArgumentChecker.missing_arguments(command, 2, arguments):
                return False
            
        elif command in ['scan', 'connect', 'kickall']:
            if ArgumentChecker.missing_arguments(command, 3, arguments):
                return False
            
        elif command in ['login', 'pinlogin', 'kick']:
            if ArgumentChecker.missing_arguments(command, 4, arguments):
                return False
            
        elif command in ['sendcmd']:
            if ArgumentChecker.missing_arguments(command, 5, arguments):
                return False
            
        return True

    
    @staticmethod
    def missing_arguments(command, number_of_arguments, arguments):
        """
        Checks if all required arguments exist.

        Args:
            command (str): Command name.
            number_of_arguments (int): Number of arguments the command has.
            arguments (list): List of arguments entered by the user.

        Returns:
            bool: True if missing arguments otherwise false.
        """

        for i in range(1, int(number_of_arguments) + 1):
            try:
                arguments[i]

            except IndexError:
                missing_argument = GetUtilities.get_translated_text(['commands', command, f'argument{i}'])
                formatted_usage = f'{GetUtilities.get_translated_text(["commands", "commandUsage"])} {command} {" ".join(["&c" + arg if arg == missing_argument else "&7&l" + arg for arg in ArgumentChecker.get_command_arguments(command)])}'
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{GetUtilities.get_translated_text(["commands", command, f"missingArgument{str(i)}"])}')
                paint(f'\n{GetUtilities.get_spaces()}{GetUtilities.get_translated_text(["prefix"])}{formatted_usage}')
                return True
            
        return False

    @staticmethod
    def get_command_indexes():
        """
        Get the command indexes.

        Returns:
            dict: A dictionary mapping command indexes to command names.
        """
        return {
            '00': 'help',
            '01': 'server',
            '02': 'uuid',
            '03': 'ipinfo',
            '04': 'dnslookup',
            '05': 'shodan',
            '06': 'websearch',
            '07': 'subdomains',
            '08': 'scan',
            '09': 'listening',
            '10': 'playerlogs',
            '12': 'fakeproxy',
            '13': 'login',
            '14': 'pinlogin',
            '15': 'sendcmd',
            '16': 'kick',
            '17': 'kickall',
            '18': 'rconbrute',
            '19': 'checker',
            '20': 'waterfall',
            '21': 'velocity',
            '22': 'connect',
            '23': 'rcon',
        }
    
    @staticmethod
    def get_command_arguments(command):
        """
        Get the arguments for a command.

        Args:
            command (str): The name of the command.

        Returns:
            list: A list of command arguments.
        """
        
        arguments = []

        for num in range(1, 11):
            if GetUtilities.get_translated_text(['commands', command, f'argument{num}']) is not None:
                arguments.append(GetUtilities.get_translated_text(['commands', command, f'argument{num}']))

        return arguments