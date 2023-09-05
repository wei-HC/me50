import nltk
import sys

FILE_MATCHES = 1
SENTENCE_MATCHES = 1


def main():

    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python questions.py corpus")

    # Calculate IDF values across files
    files = load_files(sys.argv[1])
    file_words = {
        filename: tokenize(files[filename])
        for filename in files
    }
    file_idfs = compute_idfs(file_words)

    # Prompt user for query
    query = set(tokenize(input("Query: ")))

    # Determine top file matches according to TF-IDF
    filenames = top_files(query, file_words, file_idfs, n=FILE_MATCHES)

    # Extract sentences from top files
    sentences = dict()
    for filename in filenames:
        for passage in files[filename].split("\n"):
            for sentence in nltk.sent_tokenize(passage):
                tokens = tokenize(sentence)
                if tokens:
                    sentences[sentence] = tokens

    # Compute IDF values across sentences
    idfs = compute_idfs(sentences)

    # Determine top sentence matches
    matches = top_sentences(query, sentences, idfs, n=SENTENCE_MATCHES)
    for match in matches:
        print(match)


def load_files(directory):
    """
    Given a directory name, return a dictionary mapping the filename of each
    `.txt` file inside that directory to the file's contents as a string.
    """
    mappings = {}
    files = os.listdir(directory)# 获取目录中的文件列表
    for file in files:
        with open(os.path.join(directory, file)) as f:# 使用os.path拼接文件路径
            content = f.read()# 读取文件内容
            mappings[file] = content# 将文件名映射到内容
    return mappings


def tokenize(document):
    """
    Given a document (represented as a string), return a list of all of the
    words in that document, in order.

    Process document by coverting all words to lowercase, and removing any
    punctuation or English stopwords.
    """
    stopwords = nltk.corpus.stopwords.words("english")
    # 将文档分词，将单词转换为小写，并过滤掉停用词和标点符号
    contents = [word.lower() for word in nltk.word_tokenize(document)
                if word not in stopwords and word not in string.punctuation]
    return contents

def compute_idfs(documents):
    """
    Given a dictionary of `documents` that maps names of documents to a list
    of words, return a dictionary that maps words to their IDF values.

    Any word that appears in at least one of the documents should be in the
    resulting dictionary.
    """
    doc_num = len(documents)# 文档数量
    dictionary = set()
    for words in documents.values():
        dictionary.update(words)# 创建包含所有单词的词典
    words_IDF = dict.fromkeys(dictionary)# 创建一个字典，将每个单词映射到其IDF值
    for word in dictionary:
        appears = sum([word in words for words in documents.values()])
        words_IDF[word] = math.log(doc_num/appears)

    return words_IDF


def top_files(query, files, idfs, n):
    """
    Given a `query` (a set of words), `files` (a dictionary mapping names of
    files to a list of their words), and `idfs` (a dictionary mapping words
    to their IDF values), return a list of the filenames of the the `n` top
    files that match the query, ranked according to tf-idf.
    """
    tfidfs = {}
    for file in files.keys():
        tfidf = 0
        for word in query:
            if word not in files[file]:
                continue
            tfidf += (files[file].count(word)*idfs[word])
        tfidfs[file] = tfidf
    top_n = sorted(files.keys(), key=lambda file: tfidfs[file], reverse=True)[:n]
    return top_n

def query_term_density(sent, query):
    appear = sum([word in sent for word in query])
    return appear/len(sent)

def top_sentences(query, sentences, idfs, n):
    """
    Given a `query` (a set of words), `sentences` (a dictionary mapping
    sentences to a list of their words), and `idfs` (a dictionary mapping words
    to their IDF values), return a list of the `n` top sentences that match
    the query, ranked according to idf. If there are ties, preference should
    be given to sentences that have a higher query term density.
    """
    scores = dict.fromkeys(sentences.keys())
    for sentence in sentences.keys():
        idf = 0
        for word in query:
            if word not in sentences[sentence]:
                continue
            idf += idfs[word]# 计算句子的IDF值
        scores[sentence] = idf
        # 根据IDF值和查询词密度降序排列句子
    top_n =sorted(sentences.keys(), key=lambda sentence:
    (scores[sentence], query_term_density(sentence, query)), reverse=True)[:n]
    return top_n


if __name__ == "__main__":
    main()
