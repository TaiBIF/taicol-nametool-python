## 處理流程

* 將文獻中針對分類處理區塊的**所有出現學名**依據規則以JSON格式儲存
* 只有文獻明確提到的資訊才能填入
* 不得基於推測填入任何欄位
* 如有疑問，寧願留空，也不要猜測
* 若某欄位沒有資料，直接拿掉該欄位
* 確保學名順序和文獻中一致，不得改變順序，並依據順序加上index欄位
* 當欄位有提供允許清單時（指令有「包含」），僅能填入允許清單內的值，若不在允許清單內則留空
* 特別注意必填欄位

### 對每個學名依序處理：

#### 地位處理規則

* accepted: 有效名
* not-accepted: 無效名（包含nom. nud., nom. illeg.等）
* misapplied: 誤用名（包含auct. non, non, not of, nec等）
* undetermined: 未決名，包含以下情況：
    * 種階層未確定：sp., sp. nov.?, sp. inq., sp. prox.
    * 分類地位未確定：cf., aff., ?, indet.
    * 其他未決狀態：inc. sed., stet.等

#### undetermined學名的識別

在處理學名時特別留意以下規則為undetermined學名：
* "屬名 + sp."：此筆資料rank為genus
* "屬名 + cf. + 種名"：此筆資料rank為species
* "屬名 + aff. + 種名"：此筆資料rank為species
* "屬名 + 種名 + ?"：此筆資料rank為species
* "屬名 + indet."：此筆資料rank為genus


#### is_indent規則

不管在文獻上實際有沒有縮排，都要依據下面的判斷標準決定is_indent的值

* accepted: is_indent = 0
* not-accepted, misapplied: is_indent = 1
* undetermined: 
    * 請由「分類處理 / TAXONOMIC TREATMENTS」相關區塊判斷
    * 請先判定文獻中有效名是以縮排還是粗體來表示
    * 當有效名是以縮排與否來表示：當有效學名無縮排，未決學名也無縮排：is_indent = 0，當有效學名無縮排，未決學名有縮排：is_indent = 1
    * 當有效名是以粗體與否來表示：當有效名為粗體時，未決學名也是粗體：is_indent = 0，當有效名為粗體時，未決學名是非粗體：is_indent = 1


#### 學名拆分規則

* latin_name欄位: 僅包含學名本體，不包含作者，較高階層為單名，種階層包含屬名和種小名，種下階層包含種名和種下名和種下階層(如 var.、subsp.等)，ICZN法規的subsp.需要省略，也不得包含indications。
* latin_genus欄位: 屬拉丁名。
* latin_s1欄位: 種小名，種的epithet。
* s2_rank欄位: 種下階層(如 var.、subsp.等)
* latin_s2欄位: 種下名的epithet (infraspecies epithet)。
* formatted_authors欄位: 僅包含作者，不含狀態指示詞
* indications欄位: 僅存入指定的狀態指示詞列表中的項目
* 允許的indications清單包含: nom. confus., nom. prot., nom. inval., var. nov., stet., nom. illeg., nom. nud., sensu auct., nom. nov., nom. err., nom. ambig., pro. syn., nom. alt., pro. sp., non, aff., nom. peric., nom. obl., sp. prox., ssp. nov., nom. supp., class. nov., nom. sanct., nom. perp., indet., nom. monstr., sp. nov., ex errore, nom. approb., sensu, nom. rej., fam. nov., comb. rev., corrig., nec, cf., nom. cons., gen. nov., orth. var., syn. nov., not of, auct. non, nom. dub., nom. superfl., ord. nov., ?, comb. nov., stat. rev., nom. abort., pro. hybr., orth. cons., inc. sed., unavailable, nom. manuscriptum, stat. nov., sic, sp., sp. inq., nom. rev.


#### 必要欄位

* rank: 根據學名判斷分類階層，包含：aberration,class,division,domain,epifamily,family,form,genus,grandclass,hybrid-formula,infraclass,infradivision,infrakingdom,infraorder,infraphylum,kingdom,megaclass,microphylum,mirclass,morph,nothosubspecies,nothovariety,order,parvdivision,parvphylum,phylum,race,realm,section,special-form,species,stirp,subclass,subdivision,subfamily,subform,subgenus,subkingdom,suborder,subphylum,subrealm,subsection,subspecies,subtribe,subvariety,superclass,superdivision,superfamily,superkingdom,superorder,superphylum,tribe,unranked,variety
* nomenclature: 依據學名的領域，給予對應的命名規約，如：ICZN(International Code of Zoological Nomenclature)、ICN(International Code of Nomenclature for Algae, Fungi, and Plants)、ICNP(International Code of Nomenclature of Prokaryotes)、ICVCN(International Code of Virus Classification and Nomenclature)

#### 選填欄位
* kingdom: 若可以辨別學名屬於哪個生物界，可填入此欄位，包含：Plantae,Animalia,Chromista,Fungi,Protozoa,Archaea,Bacteria,Eubacteria,Archaebacteria,Nucleariae,Zilligvirae,Heunggongvirae,Loebvirae,Sangervirae,Shotokuvirae,Trapavirae,Orthornavirae,Pararnavirae,Bamfordvirae,Helvetiavirae,Viruses

#### 模式標本處理
只有在文中明確提到Type相關字詞時才處理

* type_name: 種階層以上填入模式學名
* type_specimens: 種階層及以下，以JSON格式存入：

```
json  [{
    "use": "holotype/lectotype/syntype等",
    "kind": "標本類型，若無法判斷統一回傳數字1"
    "country": "採集國家，以英文回傳",
    "locality": "採集地點", 
    "collection_year": 年份,
    "collection_month": 月份,
    "collection_day": 日期,
    "herbarium": "館藏機構",
    "accession_number": "館號"
  }]
```

type_specimens其中use及kind為必填控制詞彙，kind請回傳括號內對應id
1. use包含：holotype, syntype, paratype, lectotype, paralectotype, neotype, topotype, allotype, type
2. kind包含：標本(1)、手繪圖(2)、生物照片(3)、DNA(4)、菌株(5)


#### 俗名格式

* common_name: `俗名(語言代碼,使用地區)`，多筆用|分隔
* 語言代碼: en-us, zh-tw, jp-jp, zh-cn, de-de, fr-fr, lat, others
* 若語言代碼為zh-tw，使用地區可以填入Taiwan，若是其他語言代碼則留空


#### 外來屬性欄位

* alien_type: 僅有下面四種native/naturalized/cultured，特別注意是以「對臺灣」而言判斷，如果分布有寫到臺灣，但沒有寫到naturalized/歸化或invasive/入侵或栽培豢養/cultured，那alien_type就是native/原生；若分布沒有台灣，就不需判斷此欄位
* 階層為屬以上（含屬本身），不需判斷此欄位

#### 屬性欄位

僅在文中明確提到時才填入，明確表示是該屬性才填1，明確表示不是該屬性才填0

* is_terrestrial: 
  - 填入1：文中明確使用「terrestrial」、「陸生」、「地生」等字詞
  - 填入0：文中明確使用「non-terrestrial」、「非陸生」等否定字詞
  - **絕對不可填入的情況**：僅描述為「epiphyte」、「附生」等，這些只是生態習性描述，不等同於明確表述陸生與否
* is_freshwater/is_brackish/is_marine/is_fossil:
  - 必須有明確的環境字詞：「freshwater/淡水」、「brackish/半鹹水」、「marine/海洋」、「fossil/化石」
  - **生態習性描述不等同於環境屬性**：如「水生植物」不等於「淡水環境」
* is_new_record: 
  - 填入1：明確使用「new record」、「首次記錄」、「新記錄」等字詞
  - **物種描述或分布擴展不等同於新記錄**
  - 特別注意當學名為新種時（sp. nov.或new species或n. sp.），忽略此欄位
* is_endemic:
  - 填入1：明確使用「endemic to Taiwan」、「臺灣特有」、「僅分布於臺灣」等字詞
  - 當填入1時，alien_type須同步填入native，is_in_taiwan同步填入1
* 階層為屬以上（含屬本身）：所有欄位都不需判斷

#### 存在於臺灣欄位：

必須滿足以下任一條件才得以標記is_in_taiwan=1：

* 文中明確寫出「Taiwan」、「臺灣」、「台灣」等地名在分布描述中
* 該分類群的標本採集地點明確標示為台灣的地點
* 文中明確描述該物種在台灣的生長環境、海拔等

需特別注意：
* 僅有中文俗名或僅列在物種清單中，但無明確分布資訊者，不得標記為 is_in_taiwan=1
* 僅在台灣文獻中被提及，但無明確分布資訊者，不得標記為 is_in_taiwan=1
* 比較性提及或僅作為分類參考的物種，但無明確分布資訊者，不得標記為 is_in_taiwan=1
* 階層為屬以上（含屬本身）的特殊情況：is_in_taiwan=2
* 僅在文中明確提到時才填入，明確表示是該屬性才填1，明確表示不是該屬性才填0



#### 存在於臺灣欄位的嚴格判斷標準：
必須滿足以下任一條件才得以標記is_in_taiwan=1：
* 文中明確寫出「Taiwan」、「臺灣」、「台灣」等地名在**分布描述段落**中
* 該分類群的標本採集地點明確標示為台灣的地點
* 文中明確描述該物種在台灣的生長環境、海拔、生態等**具體分布資訊**
* 階層為屬以上（含屬本身）的特殊情況：統一標記is_in_taiwan=2

**絕對不可標記為is_in_taiwan=1的情況：**
* 僅出現在物種清單或檢索表中
* 僅有中文俗名但無分布描述
* 僅在台灣文獻中被提及作為比較
* 僅作為分類參考或形態比較
* 模式標本來自台灣但無現生分布資訊
* 無任何台灣具體地點、環境、生態描述

**判斷流程：**
1. 先找該學名是否有明確的分布段落（Distribution:）
2. 檢查是否有台灣的具體地點、環境描述
3. 如果只是列表提及或比較提及，則不標記is_in_taiwan=1
4. 若有明確表示不存在於台灣，才可以標記is_in_taiwan=0


#### 描述欄位

* distribution: 完整擷取分布相關文字
* description: 完整擷取特徵描述文字

#### 最後檢查

在輸出最終結果前，必須逐一檢查：

1. **屬性欄位檢查**：
   - is_terrestrial, is_freshwater, is_brackish, is_marine, is_fossil, is_new_record, is_endemic 這些欄位
   - 僅在文中有「明確表述」該屬性或「明確否定」該屬性時才填入1或0
   - 如果文中只是描述相關特徵但未明確表述屬性，則完全移除該欄位

2. **indications欄位檢查**：
   - 檢查所有學名中是否包含允許清單中的指示詞
   - 特別檢查：sp., cf., aff., ?, nom. nud., auct. non, non, nec 等
   - 確保這些指示詞都正確放入indications欄位