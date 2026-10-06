**重要**：請勿自行拼湊訊息，須完全忠於提供的文件

請拆出文獻相關的資訊包含，以下資訊都要是可以確定正確的才填入，不確定或沒有提供的就留空
**沒有的欄位請直接省略該欄位，不要填入 "null"、"None"、"N/A" 等字串。**
重要：請直接回傳JSON格式，可以讓python直接使用json.load來解析，不要包含任何其他文字。

1. 文獻類型 (type)
判斷屬於下面哪一種，並回傳對應英文
    * 期刊文章：journal-article
    * 書籍文章(章節)：book-chapter
    * 書籍：book
    * 名錄：checklist

2. 作者 (author)
欄位為given, family, sequence的Array
    * **作者為必填**，通常位於文獻首頁標題下方，請依序完整列出所有作者，不可省略。
    * 中英雙語的文獻（例如同時有中文姓名「陳柏豪」與英文姓名「Po-Hao Chen」），請使用**英文（羅馬拼音）**姓名填寫：given 為「Po-Hao」，family 為「Chen」。
    * 作者姓名後的上標數字、星號（如 1、2、*）不要放入姓名。
    * given: 名
    * family: 姓氏
    * sequence: 作者排序，若為第一作者，請填入first，其餘作者皆填入additional，但仍須按照作者順序。
    格式：
    ```
    [
      {
        "given": "",
        "family": "",
        "sequence": "first",
        "affiliation": []
      },
      {
        "given": "",
        "family": "",
        "sequence": "additional",
        "affiliation": []
      },
      {
        "given": "",
        "family": "",
        "sequence": "additional",
      }
    ]
    ```
3. 發表日期 (published)
    * **至少要有年份**。年份常出現在頁首或頁尾的期刊資訊中（例如「林業研究季刊 39(2)：107-111, 2017」中的 2017）。
    * 只知道年份時填 `[[2017]]`，不要自行補上月、日。
    格式：
    ```
    {
      "date-parts": [
        [%Y, %m, %d]
      ]
    }
    ```

4. 文章標題 (title)
格式：
```
[
      "title"
    ]
```

5.  期刊/書名 (container-title)
格式：
```
[
      "container-title"
    ]
```

6. 卷號/部冊號 (volume)

7. 期號 (issue)

8. 頁碼範圍 (page)

    格式：
    ```起始頁碼-結束頁碼```

9. DOI (doi)

10. 連結 (url)

11. 語言 language
    選項包含：
    * 英文: en-us
    * 繁體中文: zh-tw
    * 日文: jp-jp
    * 簡體中文: zh-cn
    * 德文: de-de
    * 法文: fr-fr
    * 拉丁文: lat
    * 其他: others