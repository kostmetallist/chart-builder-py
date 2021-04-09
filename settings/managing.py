import abc
import json
import os
import re

from sympy import lambdify
from sympy.abc import x, y
from sympy.parsing.sympy_parser import parse_expr
from sympy.utilities.iterables import iterable

# These settings are considered as default when there is no recent session file
SETTINGS_BY_MODES = {
    'ARBITRARY_MAPPING': {
        '@ID': 1,
        'x_mapping': 'x + y',
        'y_mapping': 'y - x',
        'start_point': (1.0, -1.5),
        'iterations': 100,
    },
    'CR_SET_LOCALIZING': {
        '@ID': 2,
    },
}


# TODO function with inverted SETTINGS_BY_MODES?


class SettingsManager(abc.ABC):

    MODE = None
    RECENT_SESSION_ENCODING = 'utf-8'
    RECENT_SESSION_PATH = os.path.join('settings', '.recent_session')

    def __init__(self):
        self.settings = self._extract_cached_settings()
        self.export_overrides = dict()

    @staticmethod
    def _get_settings_from_recent_session():
        with open(SettingsManager.RECENT_SESSION_PATH,
                  encoding=SettingsManager.RECENT_SESSION_ENCODING) as f:
            return json.load(f)

    def _extract_cached_settings(self):
        return self._get_settings_from_recent_session() \
            if os.path.exists(self.RECENT_SESSION_PATH) else SETTINGS_BY_MODES

    @staticmethod
    def _parse_two_argument_function(expression: str):

        expr = parse_expr(expression)
        if any([atom.is_Symbol and atom != x and atom != y
                for atom in expr.atoms()]):

            print('Specified expression contains symbols other than x or y: '
                  f'{expr}, please enter function depending only on x and y')
            return None

        return lambdify([x, y], expr, 'numpy')

    @staticmethod
    def _parse_comma_delimited_floats(elements_number: int):
        def _parse_fixed_length_comma_delimited_floats(expression: str):

            float_re = r'[+-]?(\d*\.\d+|\d+)'
            if re.fullmatch(
                    rf'{float_re}(\s*,\s*{float_re}){{elements_number - 1}}',
                    expression):
                return [float(x) for x in expression.split(',')]
            else:
                return None

        return _parse_fixed_length_comma_delimited_floats

    @staticmethod
    def _parse_integer(expression: str):
        try:
            result = int(expression)
            return result
        except ValueError:
            return None

    @staticmethod
    def _input_with_default(default, prompt_format_string, parser_callback,
                            apply_callback_for_default=False):

        parsed_expression = None
        while parsed_expression is None:

            entered_expression = input(prompt_format_string.format(
                ', '.join([str(x) for x in default]) if iterable(default)
                else default))

            if entered_expression == '':
                parsed_expression = parser_callback(default) \
                    if apply_callback_for_default else default
                entered_expression = default
            else:
                parsed_expression = parser_callback(entered_expression)

        return entered_expression, parsed_expression

    @abc.abstractmethod
    def _prompt_user_for_settings(self):
        raise NotImplementedError

    def prompt_for_settings_and_save(self):

        print('Enter the parameters here, leave empty for defaults:')
        self._prompt_user_for_settings()
        export_prepared_settings = dict()

        for mode in self.settings:
            if mode not in self.export_overrides:
                export_prepared_settings[mode] = {**self.settings[mode]}
            else:
                export_prepared_settings[mode] = dict()

                for name in self.settings[mode]:
                    export_prepared_settings[mode][name] = \
                        self.export_overrides[mode][name] \
                        if name in self.export_overrides[mode] \
                        else self.settings[mode][name]

        with open(self.RECENT_SESSION_PATH, 'w',
                  encoding=self.RECENT_SESSION_ENCODING) as f:
            json.dump(export_prepared_settings, f,
                      indent=4, sort_keys=True)

    def retrieve_mode_settings(self):
        return self.settings[self.MODE]


class ArbitraryMappingSettingsManager(SettingsManager):

    MODE = 'ARBITRARY_MAPPING'

    def _prompt_user_for_settings(self):

        relevant_prefs = self.settings[self.MODE]
        self.export_overrides[self.MODE] = dict()
        overrides = self.export_overrides[self.MODE]

        entered, x_mapping = self._input_with_default(
            relevant_prefs['x_mapping'], 'f(x, y) [{}]: ',
            self._parse_two_argument_function, apply_callback_for_default=True)
        overrides['x_mapping'] = entered
        relevant_prefs['x_mapping'] = x_mapping

        entered, y_mapping = self._input_with_default(
            relevant_prefs['y_mapping'], 'g(x, y) [{}]: ',
            self._parse_two_argument_function, apply_callback_for_default=True)
        overrides['y_mapping'] = entered
        relevant_prefs['y_mapping'] = y_mapping

        _, start_point = self._input_with_default(
            relevant_prefs['start_point'], 'Start point [{}]: ',
            self._parse_comma_delimited_floats(2))
        relevant_prefs['start_point'] = start_point

        _, iterations = self._input_with_default(
            relevant_prefs['iterations'], 'Iterations number [{}]: ',
            self._parse_integer)
        relevant_prefs['iterations'] = iterations
