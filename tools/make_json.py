# coding=utf-8

# Copyright (c) 2018 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import json
from robot import utils


def write_format_file(fields, format_file_str):
    """
    write schema file for solr
    """
    solr_format = []
    for f in fields:
        if f == "id":
            continue
        if f == "question":
            f_type = "text_multi_lang"
            f_index = True
        else:
            f_type = "string"
            f_index = False
        f_str = {"indexed": f_index, "name": f, "stored": True, "type": f_type}
        solr_format.append(f_str)
    ff = open(format_file_str, "w")
    ff.write(json.dumps(solr_format, indent=4) + "\n")
    ff.close()


def run(faq_file_str, json_file_str):
    """
    convert text file to json file, save schema file
    """
    idx = 0
    header = 0
    field_cnt = 0
    auto_id = False
    faq_file = open(faq_file_str, "r")
    for line in faq_file:
        arr = line.strip().split("\t")
        if header == 0:
            header = 1
            field_names = arr
            field_cnt = len(field_names)
            if "question" not in field_names or "answer" not in field_names:
                print("need question and answer")
                sys.exit(6)
            if "id" not in field_names:
                auto_id = True
            # write_format_file(field_names, format_file_str)
            json_file = open(json_file_str, "w")
            continue
        if len(arr) != field_cnt:
            print(f"line {idx+2} error")
            continue
        idx += 1
        data = dict([field_names[i], arr[i]] for i in range(field_cnt))
        if auto_id:
            data["id"] = str(idx)
        json_file.write(json.dumps(data, ensure_ascii=False))
        json_file.write("\n")
    json_file.close()
    faq_file.close()


def convert(faq_str, json_file_str):
    faq_file_str = utils.write_temp_file(faq_str, ".csv", mode="w")
    run(faq_file_str, json_file_str)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python " + sys.argv[0] + " faq_file(input) json_file(output)")
        sys.exit(2)
    run(sys.argv[1], sys.argv[2])
