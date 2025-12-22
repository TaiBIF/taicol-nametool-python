from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class RankEnum(str, Enum):
    """分類階層枚舉"""
    aberration = "aberration"
    class_ = "class"
    division = "division"
    domain = "domain"
    epifamily = "epifamily"
    family = "family"
    form = "form"
    genus = "genus"
    grandclass = "grandclass"
    hybrid_formula = "hybrid-formula"
    infraclass = "infraclass"
    infradivision = "infradivision"
    infrakingdom = "infrakingdom"
    infraorder = "infraorder"
    infraphylum = "infraphylum"
    kingdom = "kingdom"
    megaclass = "megaclass"
    microphylum = "microphylum"
    mirclass = "mirclass"
    morph = "morph"
    nothosubspecies = "nothosubspecies"
    nothovariety = "nothovariety"
    order = "order"
    parvdivision = "parvdivision"
    parvphylum = "parvphylum"
    phylum = "phylum"
    race = "race"
    realm = "realm"
    section = "section"
    special_form = "special-form"
    species = "species"
    stirp = "stirp"
    subclass = "subclass"
    subdivision = "subdivision"
    subfamily = "subfamily"
    subform = "subform"
    subgenus = "subgenus"
    subkingdom = "subkingdom"
    suborder = "suborder"
    subphylum = "subphylum"
    subrealm = "subrealm"
    subsection = "subsection"
    subspecies = "subspecies"
    subtribe = "subtribe"
    subvariety = "subvariety"
    superclass = "superclass"
    superdivision = "superdivision"
    superfamily = "superfamily"
    superkingdom = "superkingdom"
    superorder = "superorder"
    superphylum = "superphylum"
    tribe = "tribe"
    unranked = "unranked"
    variety = "variety"


class NomenclatureEnum(str, Enum):
    """命名規約枚舉"""
    ICZN = "ICZN"  # International Code of Zoological Nomenclature
    ICN = "ICN"    # International Code of Nomenclature for Algae, Fungi, and Plants
    ICNP = "ICNP"  # International Code of Nomenclature of Prokaryotes
    ICVCN = "ICVCN"  # International Code of Virus Classification and Nomenclature


class StatusEnum(str, Enum):
    """學名地位枚舉"""
    accepted = "accepted"
    not_accepted = "not-accepted"
    misapplied = "misapplied"
    undetermined = "undetermined"


class AlienTypeEnum(str, Enum):
    """外來屬性枚舉"""
    native = "native"
    naturalized = "naturalized"
    cultured = "cultured"


class TypeSpecimen(BaseModel):
    """模式標本結構"""
    use: str = Field(description="標本類型：holotype/lectotype/syntype等")
    country: Optional[str] = Field(None, description="採集國家")
    locality: Optional[str] = Field(None, description="採集地點")
    collectors: Optional[str] = Field(None, description="採集者")
    collection_year: Optional[int] = Field(None, description="採集年份")
    collection_month: Optional[int] = Field(None, description="採集月份")
    collection_day: Optional[int] = Field(None, description="採集日期")
    herbarium: Optional[str] = Field(None, description="館藏機構")
    accession_number: Optional[str] = Field(None, description="館號")


class ScientificName(BaseModel):
    """學名處理結果"""
    rank: RankEnum = Field(description="分類階層")
    nomenclature: NomenclatureEnum = Field(description="命名規約")
    latin_name: str = Field(description="僅包含學名本體，不包含作者，較高階層為單名，種階層包含屬名和種小名，種下階層包含種名和種下名和種下階層(如 var.、subsp.等)，ICZN法規的subsp.需要省略。")
    latin_genus: Optional[str] = Field(None, description="屬拉丁名。")
    latin_s1: Optional[str] = Field(None, description="的epithet。")
    s2_rank: Optional[str] = Field(None, description="種下階層(如 var.、subsp.等)")
    latin_s2: Optional[str] = Field(None, description="種下名的epithet (infraspecies epithet)。")

    formatted_authors: Optional[str] = Field(None, description="作者，不含狀態指示詞")
    indications: Optional[List[str]] = Field(None, description="狀態指示詞列表")
    status: StatusEnum = Field(description="學名地位")
    is_indent: Literal[0, 1] = Field(description="縮排值：0或1")
    
    # 模式相關
    type_name: Optional[str] = Field(None, description="種階層以上填入模式學名")
    type_specimens: Optional[List[TypeSpecimen]] = Field(None, description="種階層及以下的模式標本")
    
    # 俗名
    common_name: Optional[str] = Field(None, description="俗名格式：俗名(語言代碼,使用地區)，多筆用|分隔")
    
    # 外來屬性（僅針對台灣，且僅種階層以下）
    alien_type: Optional[AlienTypeEnum] = Field(None, description="外來屬性，僅對台灣而言")
    
    # 屬性欄位（僅在明確表述時填入，僅種階層以下）
    is_terrestrial: Optional[Literal[0, 1]] = Field(None, description="是否陸生")
    is_freshwater: Optional[Literal[0, 1]] = Field(None, description="是否淡水環境")
    is_brackish: Optional[Literal[0, 1]] = Field(None, description="是否半鹹水環境")
    is_marine: Optional[Literal[0, 1]] = Field(None, description="是否海洋環境")
    is_fossil: Optional[Literal[0, 1]] = Field(None, description="是否化石")
    is_new_record: Optional[Literal[0, 1]] = Field(None, description="是否新記錄")
    is_endemic: Optional[Literal[0, 1]] = Field(None, description="是否台灣特有")
    
    # 存在於台灣（特殊規則：屬以上為2，種以下為0或1）
    is_in_taiwan: Optional[Literal[0, 1, 2]] = Field(None, description="存在於台灣：0=不存在，1=存在，2=屬以上階層")
    
    # 描述欄位
    distribution: Optional[str] = Field(None, description="完整分布描述文字")
    description: Optional[str] = Field(None, description="完整特徵描述文字")


class UsageResult(BaseModel):
    """完整的分類學處理結果"""
    scientific_names: List[ScientificName] = Field(description="所有處理的學名列表")
    
    class Config:
        use_enum_values = True  # 輸出時使用枚舉值而非枚舉對象


# 允許的狀態指示詞清單
ALLOWED_INDICATIONS = [
    "nom. confus.", "nom. prot.", "nom. inval.", "var. nov.", "stet.", 
    "nom. illeg.", "nom. nud.", "sensu auct.", "nom. nov.", "nom. err.", 
    "nom. ambig.", "pro. syn.", "nom. alt.", "pro. sp.", "non", "aff.", 
    "nom. peric.", "nom. obl.", "sp. prox.", "ssp. nov.", "nom. supp.", 
    "class. nov.", "nom. sanct.", "nom. perp.", "indet.", "nom. monstr.", 
    "sp. nov.", "ex errore", "nom. approb.", "sensu", "nom. rej.", 
    "fam. nov.", "comb. rev.", "corrig.", "nec", "cf.", "nom. cons.", 
    "gen. nov.", "orth. var.", "syn. nov.", "not of", "auct. non", 
    "nom. dub.", "nom. superfl.", "ord. nov.", "?", "comb. nov.", 
    "stat. rev.", "nom. abort.", "pro. hybr.", "orth. cons.", "inc. sed.", 
    "unavailable", "nom. manuscriptum", "stat. nov.", "sic", "sp.", 
    "sp. inq.", "nom. rev."
]

# 語言代碼對應
LANGUAGE_CODES = {
    "english": "en-us",
    "chinese_traditional": "zh-tw",
    "chinese_simplified": "zh-cn", 
    "japanese": "jp-jp",
    "german": "de-de",
    "french": "fr-fr",
    "latin": "lat",
    "others": "others"
}