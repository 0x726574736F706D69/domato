#   Domato - CSS @function / CSSFunctionDescriptors fuzzer generator
#   -----------------------------------------------------------------
#
#   Generates test cases targeting the CSS @function at-rule and the
#   CSSFunctionDescriptors CSSOM interface (Chrome 133+, behind
#   --enable-experimental-web-platform-features).
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
import sys
import argparse
from pathlib import Path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from grammar import Grammar


def generate_new_sample(template, cssgrammar):
    """Generates a single test case from the template and grammar.

    Args:
      template: Template HTML string with <cssfunctionfuzzer> placeholder.
      cssgrammar: Parsed Grammar object for css_function.txt.

    Returns:
      A string containing the generated HTML test case.
    """
    result = template

    # Generate a block of @function rules and usages for the <style> block
    css = cssgrammar.generate_root()
    result = result.replace('<cssfunctionfuzzer>', css)

    # Replace <cssfunctionfuzzer_value> with fuzzed CSS values used in JS
    # (these appear in inline strings inside the CSSOM mutation script)
    while '<cssfunctionfuzzer_value>' in result:
        value = cssgrammar.generate_symbol('css-fuzz-value')
        result = result.replace('<cssfunctionfuzzer_value>', value, 1)

    return result


def generate_samples(template, outfiles):
    """Generates a set of test case files.

    Args:
      template: Template HTML string.
      outfiles: List of output file paths to write.
    """
    rules_dir = os.path.join(os.path.dirname(__file__), '..', 'rules')
    grammar_file = os.path.join(rules_dir, 'css_function.txt')

    cssgrammar = Grammar()
    err = cssgrammar.parse_from_file(grammar_file)
    if err > 0:
        print('There were errors parsing css_function grammar')
        return

    for outfile in outfiles:
        result = generate_new_sample(template, cssgrammar)
        if result is not None:
            print('Writing a sample to ' + outfile)
            try:
                with open(outfile, 'w') as f:
                    f.write(result)
            except IOError:
                print('Error writing to output')


def get_argument_parser():
    parser = argparse.ArgumentParser(
        description='Domato CSS @function / CSSFunctionDescriptors fuzzer'
    )
    parser.add_argument(
        '-f', '--file',
        help='Output file name for a single generated test case'
    )
    parser.add_argument(
        '-o', '--output_dir',
        type=str,
        help='Output directory to write generated test cases into'
    )
    parser.add_argument(
        '-n', '--no_of_files',
        type=int,
        help='Number of test case files to generate'
    )
    parser.add_argument(
        '-t', '--template',
        type=Path,
        default=(Path(__file__).parent).joinpath('template.html'),
        help='Template HTML file to use (default: css_functions/template.html)'
    )
    return parser


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    with args.template.open('r') as f:
        template = f.read()

    if args.file:
        generate_samples(template, [args.file])

    elif args.output_dir:
        if not args.no_of_files:
            print('Please use -n to specify the number of files to generate')
        else:
            print('Running on ClusterFuzz')
            out_dir = args.output_dir
            nsamples = args.no_of_files
            print('Output directory: ' + out_dir)
            print('Number of samples: ' + str(nsamples))

            if not os.path.exists(out_dir):
                os.mkdir(out_dir)

            outfiles = []
            for i in range(nsamples):
                outfiles.append(
                    os.path.join(out_dir, 'fuzz-' + str(i).zfill(5) + '.html')
                )

            generate_samples(template, outfiles)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
