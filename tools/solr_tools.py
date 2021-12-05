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

from robot import logging
import urllib.request
import threading
import urllib
import sys
import os

logger = logging.getLogger(__name__)

HEADER = {"Content-Type": "application/json; charset=UTF-8"}
HINT_TYPE_REQ_ERR = "Request Error"
HINT_TYPE_NOR_ERR = "Error"


def _make_smart_hint(hint_type, hint_content):
    """
    Construct Tips
    """
    return "*****[{}]: {}".format(hint_type, hint_content)


def _get_error_message(respond_str):
    """
    Extract error information
    """
    print(respond_str)


def add_engine(
    host, enginename, port=8983, shard=1, replica=1, maxshardpernode=5, conf="myconf"
):
    """
    Add engine
    """
    url = "http://{}:{}/solr/admin/collections".format(host, port)
    params = {}
    params["action"] = "CREATE"
    params["name"] = enginename
    params["numShards"] = shard
    params["replicationFactor"] = replica
    params["maxShardsPerNode"] = maxshardpernode
    params["collection.configName"] = conf
    params["wt"] = "json"
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(
            req, urllib.parse.urlencode(params).encode("utf-8")
        )
        print(response.read())
    except Exception as err:
        _get_error_message(err)


def delete_engine(host, enginename, port=8983):
    """
    Delete engine
    """
    url = "http://{}:{}/solr/admin/collections".format(host, port)
    params = {}
    params["action"] = "DELETE"
    params["name"] = enginename
    params["wt"] = "json"
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(
            req, urllib.parse.urlencode(params).encode("utf-8")
        )
        print(response.read())
    except Exception as err:
        _get_error_message(err)


def upload_documents(host, enginename, port=8983, documents="", num_thread=1):
    """
    Fill documents
    documents can be a file path(Each row is a json format document)
    """

    def thread_upload(binary_data, mutex):
        """
        We didn't use the producer-consumer model because of the need to implement batch loads 
        if not, too many documents are read into memory
        """
        url = "http://{}:{}/solr/{}/update".format(host, port, enginename)
        try:
            req = urllib.request.Request(url)
            req.headers = HEADER
            response = urllib.request.urlopen(req, binary_data.encode("utf-8"))
            mutex.acquire()
            logger.info(response.read())
            mutex.release()
        except Exception as err:
            mutex.acquire()
            logger.error(err)
            mutex.release()

    def upload_batch(batch_docs):
        """
        Upload a batch of documents
        """
        if len(batch_docs[0]) <= 0:
            return
        thread_task = []
        mutex = threading.Lock()
        for sub_batch in batch_docs:
            if len(sub_batch) <= 0:
                continue
            data = "[{}]".format(",".join(sub_batch))
            task = threading.Thread(target=thread_upload, args=(data, mutex))
            task.setDaemon(True)
            thread_task.append(task)
        for task in thread_task:
            task.start()
        for task in thread_task:
            task.join()

    def upload_file(upfile):
        """
        Upload a document in a file
        """
        oneM = 2 ** 20
        batch_bytes = 0
        batch_docs = [list() for i in range(num_thread)]
        idx_container = 0
        with open(upfile) as f:
            for line in f:
                doc = line.strip()
                byte_doc = len(doc)
                # Subcontainer is not full, put in the corresponding child container
                if batch_bytes + byte_doc <= oneM:
                    batch_docs[idx_container].append(doc)
                    batch_bytes += byte_doc
                    continue
                # Sub-container space is not enough, parent container is not full, switch sub-container idx
                if idx_container + 1 < num_thread:
                    idx_container += 1
                    batch_docs[idx_container].append(doc)
                    batch_bytes = byte_doc
                    continue
                # The parent container is full, upload
                upload_batch(batch_docs)
                # clear cache
                batch_docs = [list() for i in range(num_thread)]
                idx_container = 0
                batch_docs[idx_container].append(doc)
                batch_bytes = byte_doc
            # Upload the last remaining
            upload_batch(batch_docs)

    # Based on the methods provided above, batch uploads based on incoming file types
    if os.path.isfile(documents):
        upload_file(documents)
    elif os.path.isdir(documents):
        for upfile in os.listdir(documents):
            upload_file(os.path.join(documents, upfile))
    else:
        print(_make_smart_hint(HINT_TYPE_NOR_ERR, "Wrong document file path"))


def clear_documents(host, enginename, port=8983):
    """
    delete engine
    """
    url = "http://{}:{}/solr/{}/update".format(host, port, enginename)
    params = {}
    params["stream.body"] = "<delete><query>*:*</query></delete>"
    params["wt"] = "json"
    params["commit"] = "true"
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(
            req, urllib.parse.urlencode(params).encode("utf-8")
        )
        logger.debug(response.read())
    except Exception as err:
        logger.error(err)


def help(**kwargs):
    """
    usage
    """
    print(
        """=====================================================================================
    solr_tools provides two ways to use: Python method and command line
    Commands available:
      -op             - specific operations are listed and explained below
         add_eng        -- Add a new engine
         del_eng        -- Delete a engine
         up_doc         -- Upload documents
         clear_doc      -- Clear documsnts
      -host           - hostname or host ip
      -port           - solr listenning port (default 8983)
      -eng_name       - solr engine name
      -shard          - available when op's add_eng
      -replica        - available when op's add_eng
      -nodemaxshard   - available when op's add_eng, means max shard per node
      -conf_name      - available when op's add_eng, indicate the linking conf file name
      -schema_conf    - available when op's set_schema, schema config file path
      -documents      - available when op's up_doc, documents path
      -num_thread     - available when op's up_doc, to define multithread num
    ====================================================================================="""
    )


def call_function(func, params):
    """
    call op function
    """
    func(**params)


def command_line_tools():
    """
    command tools
    """
    params = {}
    ops = {
        "add_eng": add_engine,
        "del_eng": delete_engine,
        "up_doc": upload_documents,
        "clear_doc": clear_documents,
    }
    argidx = 1
    func = help
    while argidx < len(sys.argv):
        if sys.argv[argidx] == "-op":
            op = sys.argv[argidx + 1]
            if op not in ops:
                print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
                print("Not support operation, sees:")
                print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
                help()
                exit(1)
            func = ops[op]
            argidx += 2
        elif sys.argv[argidx] == "-host":
            params["host"] = sys.argv[argidx + 1]
            argidx += 2
        elif sys.argv[argidx] == "-port":
            params["port"] = int(sys.argv[argidx + 1])
            argidx += 2
        elif sys.argv[argidx] == "-eng_name":
            params["enginename"] = sys.argv[argidx + 1]
            argidx += 2
        elif sys.argv[argidx] == "-shard":
            params["shard"] = int(sys.argv[argidx + 1])
            argidx += 2
        elif sys.argv[argidx] == "-replica":
            params["replica"] = int(sys.argv[argidx + 1])
            argidx += 2
        elif sys.argv[argidx] == "-nodemaxshard":
            params["maxshardpernode"] = int(sys.argv[argidx + 1])
            argidx += 2
        elif sys.argv[argidx] == "-conf_name":
            params["conf"] = sys.argv[argidx + 1]
            argidx += 2
        elif sys.argv[argidx] == "-schema_conf":
            params["schema_config"] = sys.argv[argidx + 1]
            argidx += 2
        elif sys.argv[argidx] == "-documents":
            params["documents"] = sys.argv[argidx + 1]
            argidx += 2
        elif sys.argv[argidx] == "-num_thread":
            params["num_thread"] = int(sys.argv[argidx + 1])
            argidx += 2
        elif sys.argv[argidx] == "-help":
            help()
            exit(1)
        else:
            help()
            exit(1)
    # call the specific op function
    call_function(func, params)


if __name__ == "__main__":
    clear_documents("localhost", "collection1", 8902)
    upload_documents(
        "localhost", "collection1", 8902, "sample_docs.json", num_thread=10
    )
