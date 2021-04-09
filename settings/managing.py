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

MODE_ID_TO_NAME = {
    SETTINGS_BY_MODES[mode]['@ID']: mode for mode in SETTINGS_BY_MODES
}


class SettingsManager(abc.ABC):

    MODE = None
    RECENT_SESSION_ENCODING = 'utf-8'
    RECENT_SESSION_PATH = os.path.join('settings', '.recent_session')

    def __init__(self):
        self.settings = self._extract_cached_settings()

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

    # FIXME doesn't allow to enter anything
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
    def _prompt_user_for_mode_settings(self):
        raise NotImplementedError

    def prompt_for_settings_and_save(self):

        print('Enter the parameters here, press <ENTER> to apply defaults:')
        export_overrides = self._prompt_user_for_mode_settings(
            self.settings[self.MODE])

        export_prepared_settings = {
            mode: {
                setting: value for setting, value in self.settings[mode].items()
            } for mode in self.settings if mode != self.MODE
        }

        # Processing overrides if any
        current_prefs = self.settings[self.MODE]
        export_prepared_settings[self.MODE] = {
            setting: (export_overrides[setting] if setting in export_overrides
                      else current_prefs[setting])
            for setting in current_prefs
        }

        with open(self.RECENT_SESSION_PATH, 'w',
                  encoding=self.RECENT_SESSION_ENCODING) as f:
            json.dump(export_prepared_settings, f,
                      indent=4, sort_keys=True)

    def retrieve_mode_settings(self):
        return self.settings[self.MODE]


class ArbitraryMappingSettingsManager(SettingsManager):

    MODE = 'ARBITRARY_MAPPING'

    def _prompt_user_for_mode_settings(self, settings):

        export_overrides = dict()

        entered, x_mapping = self._input_with_default(
            settings['x_mapping'], 'f(x, y) [{}]: ',
            self._parse_two_argument_function, apply_callback_for_default=True)
        export_overrides['x_mapping'] = entered
        settings['x_mapping'] = x_mapping

        entered, y_mapping = self._input_with_default(
            settings['y_mapping'], 'g(x, y) [{}]: ',
            self._parse_two_argument_function, apply_callback_for_default=True)
        export_overrides['y_mapping'] = entered
        settings['y_mapping'] = y_mapping

        _, start_point = self._input_with_default(
            settings['start_point'], 'Start point [{}]: ',
            self._parse_comma_delimited_floats(2))
        settings['start_point'] = start_point

        _, iterations = self._input_with_default(
            settings['iterations'], 'Iterations number [{}]: ',
            self._parse_integer)
        settings['iterations'] = iterations

        return export_overrides
