#   Domato - CSSFunctionDeclarations fuzzer generator
#   ---------------------------------------------------
#
#   Copyright 2017 Google Inc. All Rights Reserved.
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function
import os
import random
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from grammar import Grammar

_N_FUNCTIONS_MIN = 1
_N_FUNCTIONS_MAX = 10
_N_LOCAL_DECLS_MIN = 0
_N_LOCAL_DECLS_MAX = 20
_N_MUT_LINES = 20

# Known argument names for @function signatures
_FUNCTION_ARGS = ['--arg1', '--arg2', '--arg3']

# Local variable names to use in generated functions
_LOCAL_VARS = ['--local1', '--local2', '--local3', '--local4', '--local5',
               '--tmp1', '--tmp2', '--val', '--x', '--y']

# CSS length values for declarations
_LENGTH_VALUES = [
    '0', '1px', '10px', '100px', '0.5em', '2rem', '50%', '1vw', '1vh',
    'auto', 'none', 'initial', 'inherit', 'unset',
    'calc(1px + 2em)', 'calc(100% - 10px)',
]


def random_length():
    return random.choice(_LENGTH_VALUES)


def random_local_var(n_locals):
    if n_locals == 0:
        return '--local1'
    return random.choice(_LOCAL_VARS[:n_locals])


def generate_function_body(n_locals):
    """Generate the CSS text inside one @function rule body."""
    lines = []
    local_names = _LOCAL_VARS[:n_locals]

    # Add local variable declarations
    for name in local_names:
        value = random_length()
        # Occasionally make a local refer to another local
        if local_names and random.random() < 0.2:
            ref = random.choice(local_names)
            value = 'var({}, {})'.format(ref, random_length())
        lines.append('  {}: {};'.format(name, value))

    # Add result declaration
    result_choices = [random_length()]
    if local_names:
        result_choices.append('var({})'.format(random.choice(local_names)))
        result_choices.append(
            'var({}, {})'.format(random.choice(local_names), random_length()))
    result_choices.append('var(--arg1, {})'.format(random_length()))
    result_choices.append('calc(var(--arg1, 0px) + {})'.format(random_length()))
    lines.append('  result: {};'.format(random.choice(result_choices)))

    return '\n'.join(lines)


def generate_function_rules(n_functions):
    """Generate CSS text for n_functions @function rules."""
    rules = []
    for i in range(n_functions):
        name = '--fuzz-{}'.format(chr(ord('a') + i))
        n_args = random.randint(1, 3)
        args = ', '.join(
            '{}: <length>'.format(_FUNCTION_ARGS[j]) for j in range(n_args)
        )
        n_locals = random.randint(_N_LOCAL_DECLS_MIN, _N_LOCAL_DECLS_MAX)
        body = generate_function_body(n_locals)
        rules.append('@function {}({}) {{\n{}\n}}'.format(name, args, body))
    return '\n\n'.join(rules)


def generate_mutation_js(grammar, n_lines):
    """Generate JS mutation statements via the grammar."""
    code = grammar._generate_code(n_lines)
    return code


def generate_new_sample(template, grammar):
    """Generate one fuzz sample from the template."""
    result = template

    n_functions = random.randint(_N_FUNCTIONS_MIN, _N_FUNCTIONS_MAX)
    css_rules = generate_function_rules(n_functions)
    result = result.replace('<cssfunctiondeclfuzzer>', css_rules, 1)

    while '<cssfunctiondeclmutfuzzer>' in result:
        mut_js = generate_mutation_js(grammar, _N_MUT_LINES)
        result = result.replace('<cssfunctiondeclmutfuzzer>', mut_js, 1)

    return result


def generate_samples(fuzzer_dir, outfiles):
    """Generate a set of fuzz samples and write them to outfiles."""
    template_path = os.path.join(fuzzer_dir, 'template.html')
    with open(template_path) as f:
        template = f.read()

    rules_dir = os.path.join(parent_dir, 'rules')
    grammar = Grammar()
    err = grammar.parse_from_file(
        os.path.join(rules_dir, 'css_function_declarations.txt')
    )
    if err > 0:
        print('There were errors parsing css_function_declarations grammar')
        return

    for outfile in outfiles:
        result = generate_new_sample(template, grammar)
        if result is not None:
            print('Writing a sample to ' + outfile)
            try:
                with open(outfile, 'w') as f:
                    f.write(result)
            except IOError:
                print('Error writing to output')


def get_option(option_name):
    for i in range(len(sys.argv)):
        if (sys.argv[i] == option_name) and ((i + 1) < len(sys.argv)):
            return sys.argv[i + 1]
        elif sys.argv[i].startswith(option_name + '='):
            return sys.argv[i][len(option_name) + 1:]
    return None


def main():
    fuzzer_dir = os.path.dirname(os.path.abspath(__file__))

    multiple_samples = False

    for a in sys.argv:
        if a.startswith('--output_dir='):
            multiple_samples = True
    if '--output_dir' in sys.argv:
        multiple_samples = True

    if multiple_samples:
        print('Running on ClusterFuzz')
        out_dir = get_option('--output_dir')
        nsamples = int(get_option('--no_of_files'))
        print('Output directory: ' + out_dir)
        print('Number of samples: ' + str(nsamples))

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        outfiles = []
        for i in range(nsamples):
            outfiles.append(
                os.path.join(out_dir, 'fuzz-' + str(i).zfill(5) + '.html')
            )

        generate_samples(fuzzer_dir, outfiles)

    elif len(sys.argv) > 1:
        outfile = sys.argv[1]
        generate_samples(fuzzer_dir, [outfile])

    else:
        print('Arguments missing')
        print('Usage:')
        print('\tpython generator.py <output file>')
        print('\tpython generator.py --output_dir <output directory> '
              '--no_of_files <number of output files>')


if __name__ == '__main__':
    main()
