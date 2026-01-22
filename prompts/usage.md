本指令旨在將文獻中針對**分類處理區塊**的**所有出現學名**依據規則以 JSON 格式儲存。

## 1. 處理範圍與原則
* **僅納入特定章節**：只處理文章中後段分類處理結果的章節，標題通常為 Taxonomy, Taxon Account, Taxonomic Treatment, Results 等。
* **絕對真實原則**：只有文獻明確提到的資訊才能填入，**不得基於推測填入**。如有疑問，寧願留空。
* **資料完整性**：若某選填欄位沒有資料，請**直接移除該欄位**（不要回傳 null）。
* **順序性**：確保學名順序和文獻中一致，並依據順序加上 `index` 欄位。
* **有效名去重**：若學名地位為有效 (accepted)，則不得重複；所有該學名在文章中出現的屬性或描述欄位，都需彙整進同一筆資料中。
* **允許清單嚴格執行**：當欄位標示有「允許清單」時，**僅能填入清單內的值**；若文獻內容不在清單內，請留空或移除該欄位。



## 2. 輸出範例 (One-Shot Example)
請嚴格依照以下 JSON 結構回傳（此為範例，請依實際內容填寫）：

```json
[
  {
    "index": 1,
    "latin_name": "Ambrosiella beaveri",
    "rank": "species",
    "status": "accepted",
    "nomenclature": "ICN",
    "latin_genus": "Ambrosiella",
    "latin_s1": "beaveri",
    "formatted_authors": "Six, Z.W. de Beer & W.D. Stone",
    "is_indent": 0,
    "indications": ["sp. nov."],
    "type_specimens": [
       {
         "use": "holotype",
         "kind": 1,
         "country": "Taiwan",
         "locality": "Nantou County",
         "collection_year": 2015,
         "herbarium": "TNM",
         "accession_number": "F0030261"
       }
    ],
    "is_in_taiwan": 1,
    "distribution": "Distributed in Taiwan..."
  }
]
```

## 3. 輸出資料結構定義 (JSON Schema)
請對每一個提取到的學名，輸出一個包含以下欄位的 JSON 物件。

### 一、必要欄位 (Required)
以下欄位必須存在，若無法提取，請填入 null，以便後續程式篩選錯誤。

* `index`: (Integer) 學名在文獻分類區塊中出現的順序編號，從 1 開始遞增。
* `latin_name`: (String) 學名本體。
    * 規則：僅包含學名，不包含作者。
    * 較高階層為單名；種階層包含「屬名 + 種小名」；種下階層包含「屬名 + 種小名 + 種下階層 + 種下名」。
    * 指示詞處理：若帶有 indications (如 sp. nov.)，必須完全移除。
    * 特殊字樣處理：若帶有 "sp.", "spp.", "spec." 等字樣，僅保留屬名（或屬名+種名），這些字樣需忽略，絕對不可保留在 latin_name 中。
* `rank`: (String) 分類階層。
    * 判斷原則 (依優先順序)：
        1. **未決名 (Undetermined) 特殊規則 (最高優先)**：
            * "屬名 + sp." / "屬名 + indet." -> `genus`
            * "屬名 + cf./aff./? + 種名" -> `species`
        2. 文獻明確指定：
            * 若文中明確提及階層 (如 "Fam. nov.", "Order Coleoptera")，以文獻所述為準。
        3. 學名結構判斷：
            * 單名 (Uninominal) -> 依上下文判斷是否為 `genus` 或更高階層。
            * 二名 (Binomial) -> `species`。
            * 三名以上 (Trinomial+) -> 對應的 `variety` 或 `subspecies` 等。
    * 允許清單： `aberration`, `class`, `division`, `domain`, `epifamily`, `family`, `form`, `genus`, `grandclass`, `hybrid-formula`, `infraclass`, `infradivision`, `infrakingdom`, `infraorder`, `infraphylum`, `kingdom`, `megaclass`, `microphylum`, `mirclass`, `morph`, `nothosubspecies`, `nothovariety`, `order`, `parvdivision`, `parvphylum`, `phylum`, `race`, `realm`, `section`, `special-form`, `species`, `stirp`, `subclass`, `subdivision`, `subfamily`, `subform`, `subgenus`, `subkingdom`, `suborder`, `subphylum`, `subrealm`, `subsection`, `subspecies`, `subtribe`, `subvariety`, `superclass`, `superdivision`, `superfamily`, `superkingdom`, `superorder`, `superphylum`, `tribe`, `unranked`, `variety`.
* `status`: (String) 學名地位。
    * 允許清單：
        * `accepted`: 有效名。
        * `not-accepted`: 無效名（包含 nom. nud., nom. illeg. 等）。
        * `misapplied`: 誤用名（包含 auct. non, non, not of, nec 等）。
        * `undetermined`: 未決名（包含 sp., sp. nov.?, sp. inq., sp. prox., cf., aff., ?, indet., inc. sed., stet.）。
* `nomenclature`: (String) 命名規約。
    * 允許清單：
        * `ICZN`: International Code of Zoological Nomenclature (動物)。
        * `ICN`: International Code of Nomenclature for Algae, Fungi, and Plants (植物/真菌/藻類)。
        * `ICNP`: International Code of Nomenclature of Prokaryotes (原核生物)。
        * `ICVCN`: International Code of Virus Classification and Nomenclature (病毒)。

### 二、學名細節與指示詞 (Optional)
* `latin_genus`: (String) 屬名。
* `latin_s1`: (String) 種小名 (species epithet)。
* `s2_rank`: (String) 種下階層連接詞 (如 var., subsp. 等)。(注意：ICZN 法規的 subsp. 需省略)。
* `latin_s2`: (String) 種下名 (infraspecies epithet)。
* `formatted_authors`: (String) 僅包含作者，不含狀態指示詞。
* `kingdom`: (String) 生物界。
    * 允許清單： `Plantae`, `Animalia`, `Chromista`, `Fungi`, `Protozoa`, `Archaea`, `Bacteria`, `Eubacteria`, `Archaebacteria`, `Nucleariae`, `Zilligvirae`, `Heunggongvirae`, `Loebvirae`, `Sangervirae`, `Shotokuvirae`, `Trapavirae`, `Orthornavirae`, `Pararnavirae`, `Bamfordvirae`, `Helvetiavirae`, `Viruses`.
* `indications`: (Array of Strings) 狀態指示詞列表。
    * 允許清單： `nom. confus.`, `nom. prot.`, `nom. inval.`, `var. nov.`, `stet.`, `nom. illeg.`, `nom. nud.`, `sensu auct.`, `nom. nov.`, `nom. err.`, `nom. ambig.`, `pro. syn.`, `nom. alt.`, `pro. sp.`, `non`, `aff.`, `nom. peric.`, `nom. obl.`, `sp. prox.`, `ssp. nov.`, `nom. supp.`, `class. nov.`, `nom. sanct.`, `nom. perp.`, `indet.`, `nom. monstr.`, `sp. nov.`, `ex errore`, `nom. approb.`, `sensu`, `nom. rej.`, `fam. nov.`, `comb. rev.`, `corrig.`, `nec`, `cf.`, `nom. cons.`, `gen. nov.`, `orth. var.`, `syn. nov.`, `not of`, `auct. non`, `nom. dub.`, `nom. superfl.`, `ord. nov.`, `?`, `comb. nov.`, `stat. rev.`, `nom. abort.`, `pro. hybr.`, `orth. cons.`, `inc. sed.`, `unavailable`, `nom. manuscriptum`, `stat. nov.`, `sic`, `sp.`, `sp. inq.`, `nom. rev.`.
    * 檢查重點：確保 `sp.`, `cf.`, `aff.`, `?`, `nom. nud.`, `auct. non` 等皆正確提取至此。
* `is_indent`: (Integer, 0 or 1) 縮排與否判斷。
    * 核心原則：不管文獻上實際有沒有縮排，都必須優先依據以下標準決定值。
    * **依 Status 判斷 (最高優先)**：
        * `accepted`: 固定填 `0`。
        * `not-accepted`, `misapplied`: 固定填 `1`。
    * **依 Undetermined 判斷 (邏輯判定)**：
        * 僅當 status 為 `undetermined` 時，請觀察「分類處理 / TAXONOMIC TREATMENTS」區塊的排版風格進行判斷：
        * 情境 A (以「縮排」區分)：當有效名以無縮排表示
            * 若此未決學名**無縮排**：`0`
            * 若此未決學名**有縮排**：`1`
        * 情境 B (以「粗體」區分)：當有效名以粗體表示
            * 若此未決學名**也是粗體**：`0`
            * 若此未決學名**是非粗體**：`1`

### 三、模式標本 (Type Specimens)
僅在文中明確提到 Type 相關字詞時才處理。

* `type_name`: (String) 種階層以上填入模式學名。
* `type_specimens`: (Array of Objects) 種階層及以下，物件結構如下：
    * `use`: (String) 標本用途。
        * 允許清單：`holotype`, `syntype`, `paratype`, `lectotype`, `paralectotype`, `neotype`, `topotype`, `allotype`, `type`.
    * `kind`: (Integer) 標本類型代碼。
        * 允許清單：
            * `1`: 標本 (Specimen) - 若無法判斷，預設填 1。
            * `2`: 手繪圖 (Illustration)
            * `3`: 生物照片 (Photo)
            * `4`: DNA
            * `5`: 菌株 (Strain)
    * `country`: (String) 採集國家 (英文)。
    * `locality`: (String) 採集地點。
    * `collection_year`: (Integer) 年份。
    * `collection_month`: (Integer) 月份。
    * `collection_day`: (Integer) 日期。
    * `herbarium`: (String) 館藏機構。
    * `accession_number`: (String) 館號。

### 四、屬性與分布 (Properties & Distribution)
**判斷標準嚴格：僅在文中有「明確表述」或「明確否定」時才填入 1 或 0**

* `common_name`: (String) 俗名。
    * 格式：`俗名(語言代碼,使用地區)`，多筆用 `|` 分隔。(若語言代碼為 `zh-tw`，使用地區可填 `Taiwan`)。
    * 語言代碼允許清單：`en-us`, `zh-tw`, `jp-jp`, `zh-cn`, `de-de`, `fr-fr`, `lat`, `others`.

* `alien_type`: (String) 外來屬性。
    * 允許清單：
        * `native`: 原生（若分布含台灣，且無歸化/入侵/栽培等描述，預設此項）。
        * `naturalized`: 歸化。
        * `cultured`: 栽培/豢養。
        * `invasive`: 入侵。
    * 判斷邏輯：
        * 基準：僅針對「對臺灣」的屬性進行判斷。
        * 預設規則：若分佈描述中有提到臺灣 (Taiwan)，但**沒有**出現 naturalized, invasive, cultured 等字眼，則 `alien_type` 應填入 `native`。
    * 排除規則：
        1. 若分佈描述**沒有**提到臺灣，不需判斷此欄位（移除欄位）。
        2. 階層為**屬以上（含屬本身）**，不需判斷此欄位（移除欄位）。

* `is_terrestrial` / `is_freshwater` / `is_brackish` / `is_marine` / `is_fossil`: (Integer) 環境屬性。
    * 判斷標準：僅在文中有**明確使用**下列對應關鍵字時填入 `1`；有**明確使用否定**關鍵字（如 non-terrestrial）時填入 `0`。若無明確字詞，請直接移除該欄位。
    * 對應關鍵字 (必須明確出現)：
        * `is_terrestrial`: terrestrial, 陸生, 地生。
        * `is_freshwater`: freshwater, 淡水。
        * `is_brackish`: brackish, 半鹹水。
        * `is_marine`: marine, 海洋。
        * `is_fossil`: fossil, 化石。
    * 陷阱題 (**絕對不可填入的情況**)：
        * 生態習性不等於環境屬性：例如描述為 "epiphyte" (附生) **不等於** terrestrial；描述為 "aquatic plant" (水生植物) **不等於** freshwater。
    * 排除規則：
        1. 若僅有習性描述而無明確環境字詞，**必須移除該欄位**。
        2. 階層為**屬以上（含屬本身）**，不需判斷此欄位（移除欄位）。

* `is_new_record`: (Integer) 新記錄屬性。
    * 判斷邏輯：
        * 填入 1：僅在文中明確使用「new record」、「首次記錄」、「新記錄」等特定字詞時填入。
    * 排除規則 (Ignore/Remove)：
        1. **新種排除 (最優先)**：當學名為新種（標示為 `sp. nov.`, `new species`, `n. sp.` 等）時，**忽略此欄位**（即便是新記錄也不需標記，因為新種本身隱含此意）。
        2. 描述排除：一般的物種描述或分布範圍擴展，**不等同於**新記錄。
        3. 屬級排除：階層為**屬以上（含屬本身）**，不需判斷此欄位（移除欄位）。

* `is_endemic`: (Integer) 特有種屬性。
    * 判斷邏輯：
        * 填入 1：明確提及 "endemic to Taiwan"、"臺灣特有"、"僅分布於臺灣" 等字詞。
        * (連動規則：若此欄為 1，則 `alien_type` 須同步填入 `native`，且 `is_in_taiwan` 同步填入 `1`)。
    * 排除規則：階層為**屬以上（含屬本身）**，不需判斷此欄位（移除欄位）。

* `is_in_taiwan`: (Integer) 存在於臺灣。
    * 特殊規則：
        * 填入 2：階層為**屬以上（含屬本身）**。
    * 嚴格判斷流程 (針對種及種下階層)：
        1. 先確認該學名是否有明確的「分布段落 (Distribution)」。
        2. **填入 1**：必須滿足以下任一條件：
            * 文中明確寫出「Taiwan」、「臺灣」、「台灣」等地名在**分布描述段落**中。
            * 該分類群的標本採集地點明確標示為台灣的地點。
            * 文中明確描述該物種在台灣的生長環境、海拔、生態等**具體分布資訊**。
        3. **填入 0**：文中**明確表示**不存在於台灣。
    * **絕對不可標記為 1 的情況 (移除欄位)**：
        * 僅出現在物種清單或檢索表中。
        * 僅有中文俗名但無分布描述。
        * 僅在台灣文獻中被提及作為比較 (Comparison)。
        * 僅作為分類參考或形態比較。
        * 模式標本來自台灣但無現生分布資訊 (Type specimen only)。
        * 無任何台灣具體地點、環境、生態描述。

### 五、描述文字
* `distribution`: (String) 完整擷取分布相關文字。
* `description`: (String) 完整擷取特徵描述文字。

### 六、最後檢查清單
在生成 JSON 前，請自我檢查：
* `index` 是否已加上且順序正確？
* `latin_name` 是否已移除作者及 "sp." 等字樣？
* `status`, `rank`, `nomenclature`, `kingdom` 是否填入允許清單內的值？
* `is_in_taiwan` 是否符合嚴格判斷標準？
* `indications` 是否僅包含允許清單內的詞？