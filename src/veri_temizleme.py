"""
NHANES Veri Temizleme ve Birleştirme Veri Akışı
================================================
Proje Konum: Impact of Macronutrient Intake on Physical Activity Performance
Veri kaynağım: NHANES (National Health and Nutrition Examination Survey), 1988-2018

Bu script ham CSV dosyalarından sadece projemize lazım olan sütunları seçer,
eksik değer/aykırı değer temizliği yapar, dosyaları SEQN + SDDSRVYR üzerinden
birleştirir ve analiz için hazır tek bir CSV üretir:
    data_processed/analiz_verisi.csv
"""

# ENVIRONMENT SET UP
# conda'da hangi ortamdayım
# conda env list
# ortamımdaki paketleri listelemek için
# conda list
# Bu proje için kullandığım ortam: nhanes_analiz_projesi
# conda activate nhanes_analiz_projesi

import os
import numpy as np
import pandas as pd

# Görüntüleme ayarları, çok uzun olan sütun listelerini terminalde rahat görebilmek için
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 180)


# ============================================================================
# 1. DOSYA YOLLARI
# ============================================================================
# Proje kök dizinini bu dosyanın bulunduğu yere göre belirliyorum.
# Böylece script PyCharm'da hangi cwd ile çalışırsa çalışsın doğru klasörü bulmasını sağlayacak..
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data_raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data_processed')
os.makedirs(PROCESSED_DIR, exist_ok=True)

print(f"BASE_DIR       : {BASE_DIR}")
print(f"RAW_DIR        : {RAW_DIR}")
print(f"PROCESSED_DIR  : {PROCESSED_DIR}")


# ============================================================================
# 2. KULLANACAĞIM DEĞİŞKENLERİ TANIMLIYORUM
# ============================================================================
# NHANES veri sözlüğünden (dictionary_nhanes.csv) seçtiğim ilgili sütunlar.
# Dataseti küçültmek ve bellek tüketimini düşürmek için sadece bu sütunları okuyacağım.

# Demografik bilgiler (demographics_clean.csv)
DEMO_COLS = [
    'SEQN',       # Katılımcı ID
    'SDDSRVYR',   # Anket dönemi (cycle)
    'RIAGENDR',   # Cinsiyet (1=Erkek, 2=Kadın)
    'RIDAGEYR',   # Yaş (yıl)
]

# Beslenme / Makronutrient (dietary_clean.csv)
DIET_COLS = [
    'SEQN', 'SDDSRVYR',
    'DRXTKCAL',   # Enerji (kcal)
    'DRXTPROT',   # Protein (g)
    'DRXTCARB',   # Karbonhidrat (g)
    'DRXTTFAT',   # Toplam yağ (g)
]

# Fiziksel Aktivite (questionnaire_clean.csv)
# PAD615 - PAD675: günlük dakika cinsinden farklı aktivite tipleri
QUEST_COLS = [
    'SEQN', 'SDDSRVYR',
    'PAD615',     # İşte yoğun (vigorous) aktivite süresi (dk/gün)
    'PAD630',     # İşte orta (moderate) aktivite süresi (dk/gün)
    'PAD645',     # Yürüme/bisiklet ulaşım süresi (dk/gün)
    'PAD660',     # Rekreasyonel(bireyin boş zamanlarındaki) yoğun aktivite (dk/gün)
    'PAD675',     # Rekreasyonel(bireyin boş zamanlarındaki) orta aktivite (dk/gün)
]

#  Vücut Ölçümleri (response_clean.csv)
RESP_COLS = [
    'SEQN', 'SDDSRVYR',
    'BMXBMI',     # Vücut Kitle İndeksi (kg/m²)
    'BMXWT',      # Ağırlık (kg)
    'BMXHT',      # Boy (cm)
]


# ============================================================================
# 3. HAM CSV'LERİ OKUYORUM
# ============================================================================
# dosyaları büyük olduğu için read_csv'ye usecols vererek bellekte sadece istediğim sütunları tutuyorum.

print("\n Ham veri read işlemi yapıyorum")
demo = pd.read_csv(os.path.join(RAW_DIR, 'demographics_clean.csv'), usecols=DEMO_COLS)
diet = pd.read_csv(os.path.join(RAW_DIR, 'dietary_clean.csv'), usecols=DIET_COLS)
quest = pd.read_csv(os.path.join(RAW_DIR, 'questionnaire_clean.csv'), usecols=QUEST_COLS)
resp = pd.read_csv(os.path.join(RAW_DIR, 'response_clean.csv'), usecols=RESP_COLS)

print(f"demographics  : {demo.shape}")
print(f"dietary       : {diet.shape}")
print(f"questionnaire : {quest.shape}")
print(f"response      : {resp.shape}")


# ============================================================================
# 4. DIETARY VERİSİNİ KATILIMCI BAZINDA AGREGE EDİYORUM
# ============================================================================
# NHANES'de bir katılımcının birden fazla 24-saatlik beslenme kaydı (Day1, Day2)
# olabilir. Bu yüzden dietary tablosunda SEQN başına birden fazla satır var.
# Analizimizde her katılımcıya tek bir "ortalama makronutrient alımı" değeri
# vermek istiyorum, bu yüzden SEQN + SDDSRVYR'a göre groupby mean alıyorum.

print("\n Dietary tablosu katılımcı bazında ortalamasını alıyorum. ")
print(f"Önce: {diet.shape}")
diet = diet.groupby(['SEQN', 'SDDSRVYR'], as_index=False).mean(numeric_only=True)
print(f"1 katılımcı = 1 satır : {diet.shape}")


# ============================================================================
# 5. TABLOLARI BİRLEŞTİRİYORUM
# ============================================================================
# SEQN (katılımcı ID) ve SDDSRVYR (anket dönemi-cycle) ortak sütunlar üzerinden
# tüm tabloları inner-join ile birleştiriyorum. Inner join, sadece tüm
# tablolarda bulunan katılımcıları tutmakta bu da analizimi bu kişiler üzerinden yapabilmemi sağlıyor.

print("\n Tabloları birleştiriyorum (inner join, SEQN + SDDSRVYR)")
df = demo.merge(diet, on=['SEQN', 'SDDSRVYR'], how='inner')
df = df.merge(quest, on=['SEQN', 'SDDSRVYR'], how='inner')
df = df.merge(resp, on=['SEQN', 'SDDSRVYR'], how='inner')
print(f"Birleştirilmiş veri setim: {df.shape}")
print("Seçtiğim Sütunlar:", df.columns.tolist())


# ============================================================================
# HEDEF DEĞİŞKENİ (Y) ÜRETİYORUM: AKTIVITE PERFORMANSI
# ============================================================================
# Sunum modelimde "ActivityPerformance" bağımlı değişkeni kullanılıyor. NHANES
# bunu tek bir sütun maalesef yok; bunu benim oluşturmam gerekiyordu. Birkaç araştırma sonrasında gerekli bileşen formülünü kullandım.
# Kullanılan literatür standardı:
#   Toplam fiziksel aktivite süresi (dk/gün) = PAD615 + PAD630 + PAD645 + PAD660 + PAD675
# Bu, hem iş hem rekreasyon hem ulaşım kaynaklı aktivitelerin tamamını kapsamaktadır
# Yoğun aktivite (PAD615, PAD660) MET (Metabolik Eşdeğer) skoru olarak yaklaşık 2 katı sayılır;
# bu yüzden "MET-ağırlıklı performans" değişkenini de ekledim.

pad_cols = ['PAD615', 'PAD630', 'PAD645', 'PAD660', 'PAD675']

# Aktivite sütunları NaN olabilir; NaN olanları 0 saymak yerine
# "en az bir aktivite kaydı olan katılımcıyı analize alıyorum" min_count=1 şartı koyuyorum.
df['ActivityMinutes'] = df[pad_cols].sum(axis=1, min_count=1)

# MET ağırlıklı performans skoru (yoğun aktivite 2x ağırlıkta)
df['ActivityPerformance_MET'] = (
    2.0 * df[['PAD615', 'PAD660']].sum(axis=1, min_count=1).fillna(0)
    + 1.0 * df[['PAD630', 'PAD645', 'PAD675']].sum(axis=1, min_count=1).fillna(0)
)
# Hiç aktivite kaydı olmayan satırları MET sütununda da NaN olarak tutuyorum
df.loc[df['ActivityMinutes'].isna(), 'ActivityPerformance_MET'] = np.nan

print("\n Üretilen aktivite performans değişkenleri")
print(df[['ActivityMinutes', 'ActivityPerformance_MET']].describe())


# ============================================================================
# EKSİK DEĞER (MISSING VALUE) ANALİZİ
# ============================================================================
print("\n Eksik değer raporlaama ")
missing = df.isnull().sum().sort_values(ascending=False)  #DataFrame'in her hücresi için True & False döner (NaN ise True)
                                                          # her sütun için kaç tane True (yani NaN) var sayar
                                                          # büyükten küçüğe sıralar; en bozuk sütun en üstte görünür.
missing_pct = (missing / len(df) * 100).round(2)           #burada adet benim yeterli olmayacağı için % lik olarak hesaplıyoruö.
missing_df = pd.DataFrame({'eksik': missing, 'yüzde (%)': missing_pct})
print(missing_df) #burada PADxxx en eksik veri içeren değişkenlerim bu da fiziksel aktivite anketinin sadece bazı katılımcılara uygulandığını anlaşılıyor.

# Lineer Regresyon modelimin gerektirdiği temel değişkenleri zorunlu tutuyorum.
zorunlu = ['RIDAGEYR', 'RIAGENDR',
           'DRXTKCAL', 'DRXTPROT', 'DRXTCARB', 'DRXTTFAT',
           'BMXBMI', 'ActivityMinutes']

print(f"\nZorunlu sütunların hepsi dolu olan satır sayısı:")
df = df.dropna(subset=zorunlu).reset_index(drop=True)        #Sadece zorunlu listemdeki sütunlarda NaN olan satırları siler.
                                                            #Diğer sütunlardaki eksik veriler kalır.reset_index ile bozulan satırları düzene koyuyorum(0,1,2,3..)
print(f"{df.shape}")   #(36222, 18)

####### KENDİME DİPNOT #########
#   Listwise Deletion Yöntemi diğer adı ile "Complete Case Analysis"
# Avantajı: Basit, şeffaf, kolay savunulabilir. Dezavantajı: Veri kaybı.

# ============================================================================
# 8. AYKIRI DEĞER-OUTLIER TEMİZLİĞİ
# ============================================================================
# NHANES Veri Setim'de bazı kayıtlarda çok aşırı değerler var (kalori 0, BMI 100,Protein 0.. )
# Fizyolojik olarak makul aralıkları kullanacağım bunun için Dünya Sağlık Örgütü verilerini göz önünde bulundurdum:
#beslenme ve diyetetik alanında okumuş olmanın verdiği avantajlar :) eşik değerleri WHO, USDA Dietary Guidelines ve fizyoloji literatüründen geliyor.


print("\n Aykırı değer temizliği (fizyolojik makul aralıklar) ")
before = df.shape[0]

df = df[
    (df['RIDAGEYR'].between(18, 80))             # Sadece yetişkin 18-80 yaş aralığı kontrolü
    & (df['BMXBMI'].between(15, 60))             # Aşırı BMI değerleri ayırdım
    & (df['DRXTKCAL'].between(500, 6000))        # Aşırı düşük/yüksek kalori ayırdım
    & (df['DRXTPROT'].between(10, 400))
    & (df['DRXTCARB'].between(20, 800))
    & (df['DRXTTFAT'].between(5, 400))
    & (df['ActivityMinutes'].between(0, 1000))   # Günde >16 saat aktivite mantıksız, sağlıksız.
]
df = df.reset_index(drop=True) #Bu satır  ile indexleri tekrar 0,1,2,3… olarak düzenledim.

print(f"Temizlik öncesi: {before} satır")                  #Temizlik öncesi: 36222 satır
print(f"Temizlik sonrası: {df.shape[0]} satır")            #Temizlik sonrası: 28211 satır
print(f"Çıkarılan: {before - df.shape[0]} satır")          #Çıkarılan: 8011 satır


# ============================================================================
# 9. KATEGORIK ETIKETLEMELER -
# ============================================================================
df['Cinsiyet'] = df['RIAGENDR'].map({1: 'Erkek', 2: 'Kadın'})

# Yaş grupları
bins = [17, 29, 44, 59, 80]
labels = ['18-29', '30-44', '45-59', '60-80']
df['YasGrubu'] = pd.cut(df['RIDAGEYR'], bins=bins, labels=labels)

# BMI kategorisi (WHO litaratüründe tanımı )
def bmi_kategorisi(bmi):
    if bmi < 18.5:
        return 'Zayıf'
    elif bmi < 25:
        return 'Normal'
    elif bmi < 30:
        return 'Fazla kilolu'
    else:
        return 'Obez'
df['BMI_Kategori'] = df['BMXBMI'].apply(bmi_kategorisi)

# Makronutrient yüzdelikleri — kalori başına oran (literatür standardı)
df['Protein_Pct'] = (df['DRXTPROT'] * 4 / df['DRXTKCAL']) * 100
df['Carb_Pct'] = (df['DRXTCARB'] * 4 / df['DRXTKCAL']) * 100
df['Fat_Pct'] = (df['DRXTTFAT'] * 9 / df['DRXTKCAL']) * 100


# ============================================================================
# 10. BETIMSEL ISTATISTIKLER
# ============================================================================
# Sayısal değişkenler için ayrı bir tanımlama yapıyorum.
# Sadece gerçek sayısal (numeric) tipler — kategorik/object dışarıda kalacak şekilde.
num_var = [col for col in df.select_dtypes(include=np.number).columns
           if col not in ['SEQN', 'SDDSRVYR']]

# Temel descriptive fonksiyonlarını listeliyorum
desc_agg = ['count', 'mean', 'std', 'min', 'max']
desc_agg_dict = {col: desc_agg for col in num_var}
desc_summ = df[num_var].agg(desc_agg_dict)

print("\n Betimsel İstatistikler")
print(desc_summ.T.round(2))

#RIAGENDR mean = 1.48 olduğu için %48 kadın %52 erkek dengeli bir dağılım sözkonusu diyebilriz.
#RIDAGEYR ortalama 45 yaş std 18 tüm yaş bantlarını içeren homojen yetişkin grubu ele alınmış demektir.
#BMXBMI = 28.45 bu kritik bir bilgi: Ortalama BMI 28.45 — fazla kilolu (25-30) sınırında, neredeyse obez amerika için doğal denilebilir.


# ============================================================================
# 11. KAYIT TİME!!
# ============================================================================
out_path = os.path.join(PROCESSED_DIR, 'analiz_verisi.csv')
df.to_csv(out_path, index=False)
print(f"\n Yehuu :d Analiz verisi kaydedildi: {out_path}")
print(f"  Boyut: {df.shape[0]} satır × {df.shape[1]} sütun")        #Boyut: 28211 satır × 24 sütun