# Module 3: AI Vector Search with DocumentDB

**Duration:** 60-90 minutes | **Goal:** Understand and implement vector search using DocumentDB's integrated DiskANN indexing.

## What You'll Learn

- 🎯 What is vector search and why it matters
- 🚀 DiskANN algorithm - Microsoft's breakthrough for billion-scale search
- 📊 Comparing vector index types (IVF, HNSW, DiskANN)
- 🔍 Implementing filtered vector search with metadata
- 💡 Best practices for vector search at scale

---

## Prerequisites

✅ Completed Module 1 (DocumentDB cluster running)  
✅ Completed Module 2.1, 2.2, 2.3 (NoSQL fundamentals)  
✅ Sample data: `movie-data/movies_with_vectors.json` (pre-generated with 256-dimensional embeddings)  
✅ DocumentDB VS Code Extension (for importing data)

---

## What's in This Module

This module uses a **movie dataset** with 50 popular films and pre-computed embeddings (256 dimensions from Azure OpenAI text-embedding-3-small). You'll learn vector search by finding similar movies based on semantic meaning.

**Note:** The embeddings and query vectors are already generated - you don't need Azure OpenAI access for this module. Simply import the data and start searching!

### Folder Structure

```
3-AI-Vector-Search/
├── README.md                                  # This file
└── movie-data/
    ├── movies_with_vectors.json               # 50 movies with 256-dim embeddings (ready to import)
    ├── query_embeddings.json                  # Pre-generated query vectors for search
    ├── movies_input.ndjson                    # Original movie data (without embeddings)
    ├── generate_movie_embeddings.py           # Script used to generate embeddings (reference only)
    └── generate_query_embeddings.py           # Script used to generate query vectors (reference only)
```

**Python Scripts:** The `.py` files show how embeddings were generated using Azure OpenAI. You don't need to run them - all outputs are included. Keep your `.env` file in `.gitignore` to protect API keys.

**Optional:** After completing the basics, explore the healthcare industry example at [Industry-solutions/health-care-vector-search](../Industry-solutions/health-care-vector-search/README.md) for medical research papers, patient records, and clinical notes with vector embeddings.

---

## Part 1: Understanding Vector Search (15 minutes)

### What is Vector Search?

**Traditional Search:**
```javascript
// Exact keyword match
db.products.find({ name: { $regex: "laptop" } })
```

**Vector Search:**
```javascript
// Semantic similarity search
db.products.aggregate([{
  $search: {
    cosmosSearch: {
      vector: [0.52, 0.28, 0.12, ...], // 1536 dimensions
      path: "description_embedding",
      k: 5  // Top 5 most similar
    }
  }
}])
```

**Key Differences:**
- **Keyword:** Finds exact word matches → "laptop" won't find "portable computer"
- **Vector:** Finds semantic meaning → understands concepts, synonyms, context

### Real-World Use Cases

| Use Case | Traditional Search | Vector Search |
|----------|-------------------|---------------|
| Product Discovery | "red shoes" | "something for a wedding" |
| Medical Research | exact diagnosis code | similar symptoms/conditions |
| Customer Support | ticket category | semantic similarity of issues |
| Fraud Detection | rule-based patterns | anomaly detection via embeddings |

---

## Part 2: Vector Index Algorithms (20 minutes)

DocumentDB supports **three vector index types** - choosing the right one depends on your scale and requirements.

### Algorithm Comparison

| Feature | IVF | HNSW | DiskANN |
|---------|-----|------|---------|
| **Best For** | <10K vectors | <50K vectors | 50K+ to billions |
| **Memory Usage** | Low | High | Low (disk-based) |
| **Search Speed** | Fast | Very Fast | Fast |
| **Recall Accuracy** | ~85% | ~95% | >95% |
| **Build Time** | Fast | Slow | Medium |
| **Min Tier** | M10/M20 | M30+ | M30+ |

### Why DiskANN is Revolutionary

**DiskANN** (Disk-based Approximate Nearest Neighbor) is a Microsoft Research algorithm that solves the billion-scale vector search problem:

**Traditional Problem:**
- HNSW: Requires all vectors in RAM → 1B vectors × 1536 dims × 4 bytes = **6TB RAM** 💰💸
- IVF: Fast but lower accuracy (~85% recall)

**DiskANN Solution:**
- Stores vectors on disk (SSD)
- Loads only needed vectors into memory
- Graph-based navigation for efficient search
- **>95% recall** at <50ms latency
- Supports up to **16,000 dimensions** (with product quantization)

**How DiskANN Works:**
1. **Build Phase:** Creates graph structure connecting similar vectors
2. **Search Phase:** Navigates graph from entry point → loads relevant disk pages → finds neighbors
3. **Optimization:** Only loads 1-5% of vectors into memory per query

**Key Parameters:**
```javascript
{
  kind: "vector-diskann",
  dimensions: 1536,           // Vector size
  similarity: "COS",          // COS, L2, or IP
  maxDegree: 32,              // Graph edges (20-2048)
  lBuild: 64                  // Build quality (10-500)
}
```

- **maxDegree:** Higher = better accuracy, slower builds (32 is balanced)
- **lBuild:** Higher = better index quality, longer build time (64 is balanced)

---

## Part 3: Hands-On Vector Search (35 minutes)

### 3.1 Load Movie Dataset

The movie dataset with embeddings is ready to import. Use the **DocumentDB VS Code Extension** for easy import.

**Step 1: Import using DocumentDB Extension**

1. Open VS Code's **DocumentDB Extension** (in the sidebar)
2. Connect to your DocumentDB cluster (if not already connected)
3. Navigate to your cluster → `trainingdb` database → `movies` collection
4. Right-click on `movies` collection → **Import Documents into Collection...**
5. Select the file: `3-AI-Vector-Search/movie-data/movies_with_vectors.json`
6. Wait for import to complete (should take ~10 seconds for 50 movies)

**Step 2: Verify the data**

Use **DocumentDB Scrapbook** to run queries:
- Right-click on your cluster → **DocumentDB Scrapbook**
- Copy and paste the queries below
- Click the **Run Command** button above each query block
- Or click **Run All** at the top to execute all commands

```javascript
use trainingdb

db.movies.countDocuments()  // Should return: 50

// Check a sample document
db.movies.findOne({title: "Inception"})

// Verify embedding exists and has 256 dimensions
db.movies.findOne(
  {title: "Inception"}, 
  {title: 1, contentVector: 1, _id: 0}
).contentVector.length  // Should return: 256
```

### 3.2 Create DiskANN Vector Index

Use **DocumentDB Scrapbook** to create the index:

```javascript
db.runCommand({
  createIndexes: "movies",
  indexes: [{
    name: "vector_index",
    key: { contentVector: "cosmosSearch" },
    cosmosSearchOptions: {
      kind: "vector-diskann",
      dimensions: 256,  // Our embeddings are 256-dimensional
      similarity: "COS"
    }
  }]
})
```

**Response:** `{ ok: 1 }`

**Verify index creation:**
```javascript
db.movies.getIndexes()
```

⏱️ **Index creation takes ~1-2 minutes for 50 documents**

### 3.3 Perform Vector Search with Pre-Generated Query

Now let's search for movies! We'll use **pre-generated query embeddings** for common search scenarios - all embedding values are included below so you can copy-paste directly.

**Scenario 1: "Find mind-bending sci-fi thrillers"**

We want movies similar to Inception or The Matrix. The query embedding for *"mind-bending sci-fi thriller with complex plot"* is included below:

```javascript
// Pre-generated embedding for: "mind-bending sci-fi thriller with complex plot"
// Expected matches: Inception, The Matrix, Interstellar
const queryVector = [-0.06071380898356438,0.13644841313362122,-0.17841489613056183,-0.001474488410167396,-0.06117245927453041,-0.021054906770586967,0.050422847270965576,-0.028221314772963524,0.006976498290896416,-0.11810240149497986,0.05727393180131912,-0.05844922363758087,-0.06638960540294647,-0.029281942173838615,0.04652431979775429,-0.034427423030138016,-0.0907553881406784,-0.07281070202589035,-0.030471567064523697,0.054063379764556885,-0.030156243592500687,-0.0014135739766061306,0.08754483610391617,0.10606283694505692,-0.013716504909098148,-0.004013188648968935,-0.06948549300432205,0.06971481442451477,0.004525586497038603,0.12773405015468597,0.035975366830825806,-0.03179018571972847,0.045320361852645874,-0.1287660151720047,-0.04689697176218033,-0.012827870436012745,-0.060885801911354065,-0.014397313818335533,-0.018675658851861954,-0.02558407559990883,-0.09098471701145172,0.034742746502161026,0.002698152558878064,0.07218006253242493,0.004858824424445629,-0.023161830380558968,-0.05082416534423828,0.09534189105033875,0.05916586518287659,0.1077827736735344,-0.06925616413354874,-0.00587287126109004,-0.07888782024383545,0.19939813017845154,-0.12784871459007263,0.1436721384525299,-0.07458797097206116,0.06317905336618423,0.08141039311885834,-0.013816834427416325,0.008714351803064346,-0.08009177446365356,0.05334674194455147,0.17417237162590027,0.0064605167135596275,0.029582932591438293,-0.0062025259248912334,-0.04345709830522537,0.0435144305229187,0.01004013791680336,0.03141753375530243,0.06908417493104935,-0.03947257623076439,0.08026377111673355,0.020037276670336723,-0.013035695999860764,0.04999286308884621,-0.04729829356074333,-0.08043576031923294,-0.03958723694086075,-0.04033254459500313,-0.06656159460544586,0.11173862963914871,0.05136881023645401,0.00448975432664156,0.032076843082904816,-0.08811815083026886,-0.04709763452410698,-0.1928623765707016,-0.0968325063586235,0.076823890209198,0.07046012580394745,-0.04414507374167442,0.0762505829334259,0.012376386672258377,0.02516842447221279,0.04649565368890762,0.04953421279788017,-0.005647129379212856,0.08267167955636978,0.031646858900785446,-0.08009177446365356,0.03866993635892868,0.04615166783332825,0.10262296348810196,0.04147917032241821,-0.01109359972178936,0.008227036334574223,0.0290526170283556,0.08141039311885834,-0.12853668630123138,0.02112657018005848,-0.08691419661045074,0.03577470779418945,-0.0061846100725233555,-0.01983661763370037,0.07888782024383545,-0.06484165787696838,0.12658743560314178,0.024738440290093422,0.019234638661146164,-0.038583941757678986,-0.054751355201005936,0.0468396432697773,0.027490340173244476,-0.03617602586746216,-0.016009755432605743,-0.028679965063929558,-0.0210692398250103,0.06186043471097946,-0.009896809235215187,-0.020653586834669113,0.00038004358066245914,-0.09430992603302002,0.021155236288905144,0.005457219667732716,-0.07109076529741287,0.0294969342648983,-0.011437587440013885,0.08634088188409805,-0.060083165764808655,0.024079130962491035,0.008012044243514538,0.006700591184198856,0.08771683275699615,0.10503087192773819,0.0003529455862008035,0.041106514632701874,0.013179023750126362,0.010606283321976662,0.029697595164179802,0.008578190580010414,-0.05420671030879021,0.0370359942317009,0.07298269867897034,0.024136461317539215,-0.04503370821475983,0.008105207234621048,0.014863129705190659,-0.05300275236368179,-0.011086433194577694,-0.10422823578119278,0.04807226359844208,-0.07894515246152878,0.015536772087216377,0.08404763042926788,-0.022101201117038727,0.0458650104701519,-0.048874903470277786,0.052400775253772736,-0.0006418413831852376,-0.06891217827796936,-0.09998572617769241,-0.08186904340982437,0.10084569454193115,0.11363056302070618,0.12830737233161926,-0.17222312092781067,-0.042797788977622986,-0.05870721489191055,0.04560701921582222,0.05910853296518326,-0.004665331449359655,0.06449767202138901,-0.008463528007268906,-0.0393005795776844,-0.03686400130391121,0.03445608913898468,0.003769530449062586,0.053203411400318146,-0.012204392813146114,0.09373661875724792,0.04577901214361191,0.007313319481909275,0.04199514910578728,-0.07097610086202621,0.11655446141958237,0.03285081312060356,-0.019191639497876167,0.023763809353113174,-0.016282077878713608,0.013566010631620884,-0.03803929314017296,0.022545520216226578,0.021226899698376656,0.02595672942698002,0.03680667281150818,0.022975504398345947,-0.06982947885990143,0.03548805043101311,0.09006741642951965,-0.013286520726978779,-0.08657021075487137,0.08204104006290436,0.04004588723182678,0.020295267924666405,0.038325950503349304,0.007969046011567116,-0.004801493138074875,0.07504662126302719,0.02503942884504795,-0.0007780031301081181,0.015020791441202164,0.08794615417718887,0.13805368542671204,0.054264042526483536,0.06558696180582047,-0.008356031961739063,0.015092454850673676,0.1448187679052353,0.021427558735013008,-0.00966748408973217,-0.002979434095323086,0.07223739475011826,0.03067222610116005,0.0876021683216095,-0.048616912215948105,0.0014216362033039331,0.028049319982528687,-0.057531923055648804,0.026014061644673347,-0.004984236788004637,-0.033366795629262924,-0.017830023542046547,-0.025684405118227005,-0.05543933063745499,-0.01449764333665371,0.044890377670526505,-0.06208975985646248,0.025612741708755493,0.023878471925854683,0.08909278362989426,0.0028880625031888485,-0.061000462621450424,0.023276492953300476,0.0030475149396806955];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,  // Use the pre-generated embedding
        path: "contentVector",
        k: 5
      }
    }
  },
  {
    $project: {
      title: 1,
      genre: 1,
      description: 1,
      year: 1,
      rating: 1,
      score: { $meta: "searchScore" }
    }
  }
])
```

**Expected Results:**
```javascript
[
  { title: "Inception", genre: "Sci-Fi", score: 0.92, year: 2010 },
  { title: "The Matrix", genre: "Sci-Fi", score: 0.89, year: 1999 },
  { title: "Interstellar", genre: "Sci-Fi", score: 0.86, year: 2014 },
  { title: "The Prestige", genre: "Drama", score: 0.81, year: 2006 },
  { title: "Fight Club", genre: "Drama", score: 0.78, year: 1999 }
]
```

💡 **What happened?** The vector search found movies with similar semantic meaning - not just matching the word "sci-fi", but understanding concepts like "complex plot", "mind-bending", and "thriller".

### 3.4 More Search Scenarios

**Scenario 2: "Find heartwarming animated family movies"**

```javascript
// Pre-generated embedding for: "heartwarming animated family movie"
// Expected matches: Toy Story, Finding Nemo, The Lion King
const queryVector = [0.013281506486237049,0.045708734542131424,-0.10512740910053253,0.03815755620598793,-0.06426535546779633,-0.11942645162343979,-0.10180703550577164,0.1353856772184372,0.0020735617727041245,-0.08932884782552719,0.03481040149927139,0.043164897710084915,-0.10127148777246475,-0.02632201835513115,-0.02389867976307869,0.08102790266275406,-0.0005280135083012283,-0.056981947273015976,-0.002113727619871497,0.021756500005722046,0.04021940007805824,-0.01767297275364399,-0.03167746588587761,0.015292882733047009,0.0030756555497646332,-0.048174321651458740.06898964196443558,0.05566084012389183,0.011822815798223019,0.00876551866531372,0.021584836393594742,-0.06392136961221695,0.0651919022202492,-0.03524305671453476,-0.01827918179333210.03926684707403183,-0.06392136961221695,-0.0382698029279709,0.002354892250150442,-0.04611835628747940.10545139759778976,0.026377664133906364,-0.027407646179199219,0.03992015495896339,0.049462027102708816,-0.05663551390171051,-0.09969350695610046,0.0954193025827408,0.027751306444406509,0.09068008512258530.023215869441628456,-0.021842494606971741,-0.03972582519054413,0.15077614784240723,-0.01756014674901962,0.0749862715601921,-0.016880549863725901,0.03869354724884033,0.01709518954157829,0.04859101027250290.03298879414796829,-0.03752393275499344,0.0669502243399620.12327513098716736,-0.02271536923944950.06898964196443558,0.08041656762361526,-0.06048871949315071,-0.059373933821916580.0075731184333562851,-0.07098965346813202,0.07672426104545593,-0.05509220436215401,-0.037609595060348511,0.010491855256259441,0.03649328649044037,0.07387233525514603,-0.08358320593833923,-0.04534969106316566,-0.020297853276133537,-0.06615803390741348,0.16279622912406921,0.018212536349892616,0.017585551738739014,0.09239571541547775,-0.04112304747104645,-0.10581505298614502,-0.21072734892368317,-0.1088156923651695,0.010706348530948162,0.04073039814829826,-0.06804431974887848,0.06838830560445786,0.041036397218704224,0.04879534244537354,-0.05000346526503563,0.08186853677034378,0.053494457900524139,0.020898517593741417,0.016622891649603844,-0.07244438678026199,-0.015378545410931110.034161269664764404,0.08692848682403564,0.004915080685168505,0.0377840893864631653,0.050577707588672638,-0.07732090353965759,0.01565007492899895,-0.09998749196529388,0.02797201834619045,0.007337454520165920.03655611351132393,-0.014176900684833527,0.02734159119427204,-0.013189844340085983,0.00014619947457592934,0.028437627851963043,0.012367971055209637,-0.06563472747802734,0.021842494606971741,0.046567052602767944,0.08209569752216339,0.00752029474824667,0.005959577113389969,-0.018641861155629158,-0.041380055248737335,0.010148850269615650.01709518954157829,-0.04483637958765030.038699213415384293,0.013060346990823746,-0.04209101572632790.0835259035229683,0.026892995834350586,0.016193566843867302,-0.03326245397329330.0383127974271774,-0.029124621301889420.04083756357431412,-0.09711215645074844,0.0017284683464095,-0.01695235259830952,0.0478193350136280.06752100586891174,0.0383127974271774,-0.05303939059376717,-0.07213206589221954,-0.059888262301683426,0.01657856814563274,-0.08589385449886322,0.045794397592544556,-0.06072587892413139,0.024432979524135590.08089588582515717,-0.005072738509625196,-0.02623485215008259,-0.017414389923214912,0.021842494606971741,0.0378697894513607,-0.004657422471791506,0.04483637958765030.026463661715388298,-0.03064347617328167,-0.01603555865585804,0.01800552010536194,0.02797201834619045,0.13071982562541962,-0.10786300897598267,0.019500179961323738,0.04037641733884811,0.06201042234897614,-0.036837261170148849,0.07084681838750839,0.00437537580728531,0.05912116914987564,-0.012883302755653858,-0.02192157506942749,-0.04092473536729813,-0.00007370923389727250.017671212553977966,0.055252604186534882,0.04897933825850487,0.017070729657173157,0.03798623010516167,-0.0655219480395317,0.1126878559589386,0.057010751217603683,0.03252081200480461,0.04345559701323509,-0.02797201834619045,-0.0059059108607470989,0.01565007492899895,0.05697949975728989,0.024690637737512589,0.049977358430624008,0.04517536237835884,0.02574153430759907,0.08778511732816696,0.040348969399929047,0.08347604423761368,-0.019500179961323738,0.0070875641889870167,-0.09252855181694031,0.01709518954157829,0.011308319307863712,-0.03766677156090736,-0.06046013906598091,-0.05457889661192894,0.015163218788802624,0.041380055248737335,-0.03378576785326004,0.04654301330447197,0.04843817651271820.036665264517068863,0.015120383910834789,-0.08912748843431473,-0.027579145133495331,-0.004207679908722639,0.11028003692626953,-0.06563472747802734,-0.06006636843085289,-0.09711215645074844,-0.1076916903257370.05383693054318428,-0.0006179282162338495,0.00036776356864720583,-0.03438071161508560.0030328811798244715];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 5
      }
    }
  },
  { $project: { title: 1, genre: 1, year: 1, score: { $meta: "searchScore" } } }
])
```

**Expected:** Toy Story, Finding Nemo, The Lion King, The Incredibles, Spirited Away

**Scenario 3: "Find intense crime dramas with mob violence"**

```javascript
// Pre-generated embedding for: "intense crime drama with mob violence"
// You can find this in movie-data/query_embeddings.json
const queryVector = [/* copy from query_embeddings.json */];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 5
      }
    }
  },
  { $project: { title: 1, genre: 1, director: 1, score: { $meta: "searchScore" } } }
])
```

**Expected:** The Godfather, Goodfellas, The Departed, Pulp Fiction, Casino Royale

💡 **More Query Embeddings Available!** See `movie-data/query_embeddings.json` for additional pre-generated search queries including:
- "epic fantasy adventure with battles"
- "psychological thriller with dark atmosphere"

### 3.5 Filtered Vector Search

Combine semantic search with metadata filters:

**Search: "Mind-bending sci-fi" + Only movies after 2000**

```javascript
const queryVector = [/* mind-bending sci-fi embedding */];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 10,
        filter: {
          year: { $gte: 2000 }  // Only movies from 2000 onwards
        }
      }
    }
  },
  { $project: { title: 1, year: 1, genre: 1, score: { $meta: "searchScore" } } }
])
```

**Search: "Action movies" + Rating above 8.0**

```javascript
db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 10,
        filter: {
          $and: [
            { genre: { $eq: "Action" } },
            { rating: { $gte: 8.0 } }
          ]
        }
      }
    }
  },
  { $project: { title: 1, rating: 1, director: 1, score: { $meta: "searchScore" } } }
])
```

### 3.6 About the Pre-Generated Query Embeddings

All query embeddings are available in `movie-data/query_embeddings.json`. This file contains multiple search scenarios with their embeddings already computed.

**File Structure:**
```json
[
  {
    "query": "mind-bending sci-fi thriller with complex plot",
    "description": "Looking for movies like Inception or The Matrix",
    "expected_matches": ["Inception", "The Matrix", "Interstellar"],
    "embedding": [-0.0607, 0.1364, -0.1784, ...]  // 256 dimensions
  },
  {
    "query": "heartwarming animated family movie",
    "description": "Family-friendly animation with emotional story",
    "expected_matches": ["Toy Story", "Finding Nemo", "The Lion King"],
    "embedding": [0.0132, 0.0457, -0.1051, ...]  // 256 dimensions
  }
  // ... more queries
]
```

**To use a query embedding:**
1. Open `movie-data/query_embeddings.json`
2. Find the query that matches your search intent
3. Copy the entire `embedding` array (all 256 numbers)
4. Paste it as the `vector` value in your `cosmosSearch` query

**How These Were Generated (Reference Only):**

The Python scripts in the `movie-data/` folder show how these embeddings were created:

```powershell
# These commands are for reference - you don't need to run them!
# All outputs are already included in the repository

cd movie-data

# Generate movie embeddings (produces movies_with_vectors.json)
python generate_movie_embeddings.py

# Generate query embeddings (produces query_embeddings.json)  
python generate_query_embeddings.py
```

**Important:** If you explore the Python scripts, remember to keep `.env` files in `.gitignore` to protect your Azure OpenAI API keys and connection strings.

---

## Part 4: Understanding Query Parameters (10 minutes)

### Key Parameters Explained

**k (number of results):**
```javascript
k: 5  // Return top 5 most similar documents
```

**lSearch (candidate list size):**
```javascript
lSearch: 40  // Check 40 candidates to find top k results
```

**Guidelines:**
- Start with `lSearch = 4 × k` (e.g., k=10 → lSearch=40)
- Increase lSearch for better accuracy (higher recall)
- Higher lSearch = slower queries but better results

**Similarity Metrics:**

| Metric | Use Case | Range |
|--------|----------|-------|
| **COS** (Cosine) | Text embeddings, normalized vectors | -1 to 1 |
| **L2** (Euclidean) | Images, absolute distance matters | 0 to ∞ |
| **IP** (Inner Product) | Recommendations, unnormalized | -∞ to ∞ |

**Best Practice:** Use **COS** for most text-based applications

---

## Part 5: Practice Exercises (15 minutes)

### Exercise 1: Find Epic Fantasy Adventures
Search for movies similar to "epic fantasy adventure with battles"

**Hint:** Use the pre-generated query embedding from `query_embeddings.json`

<details>
<summary>Solution</summary>

```javascript
// Copy embedding for "epic fantasy adventure with battles" from query_embeddings.json
const queryVector = [/* paste embedding here */];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 5
      }
    }
  },
  { $project: { title: 1, genre: 1, year: 1, score: { $meta: "searchScore" } } }
])
```

**Expected:** The Lord of the Rings, Braveheart, Gladiator, Avatar, Star Wars
</details>

### Exercise 2: Filter by Release Year
Find "psychological thrillers" released after 2010

<details>
<summary>Solution</summary>

```javascript
const queryVector = [/* psychological thriller embedding */];

db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 10,
        filter: {
          year: { $gte: 2010 }
        }
      }
    }
  },
  { $project: { title: 1, year: 1, genre: 1, score: { $meta: "searchScore" } } }
])
```
</details>

### Exercise 3: High-Rated Action Movies
Find action movies with rating >= 8.5

<details>
<summary>Solution</summary>

```javascript
// Use action movie query embedding
db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,
        path: "contentVector",
        k: 10,
        filter: {
          $and: [
            { genre: { $in: ["Action", "Sci-Fi"] } },
            { rating: { $gte: 8.5 } }
          ]
        }
      }
    }
  },
  { $project: { title: 1, rating: 1, genre: 1, score: { $meta: "searchScore" } } }
])
```

**Expected:** The Dark Knight, Interstellar, Inception, Gladiator
</details>

### Exercise 4: Compare Traditional vs Vector Search

**Traditional keyword search:**
```javascript
db.movies.find({ 
  $or: [
    { description: { $regex: /sci-fi/i } },
    { genre: "Sci-Fi" }
  ]
}).limit(5)
```

**Vector semantic search:**
```javascript
// Search: "space exploration and future technology"
db.movies.aggregate([
  {
    $search: {
      cosmosSearch: {
        vector: queryVector,  // Pre-generated embedding
        path: "contentVector",
        k: 5
      }
    }
  }
])
```

**Question:** What's the difference in results? Why does vector search return better matches?

---

## Advanced: Healthcare Industry Example (Optional)

Want to explore **real-world vector search** with pre-embedded healthcare data?

### Healthcare Use Case

The `healthcare/` subfolder contains a complete industry example with pre-generated embeddings (256 dimensions):
- **Medical research papers** with semantic search
- **Patient records** combining demographics, diagnoses, medications, and clinical notes
- **Medical knowledge articles** with treatment information

**Note:** Like the movie dataset, all embeddings are pre-generated - you don't need Azure OpenAI access!

```
3-AI-Vector-Search/
├── README.md                              # This file
└── healthcare/                            # Healthcare industry example
    ├── README.md                          # Healthcare setup and query guide
    ├── generate_healthcare_embeddings.py  # Script showing how embeddings were generated
    ├── data/                              # Source data (shows data combination)
    ├── ResearchPapers_with_vectors.json   # Ready to import
    ├── PatientRecords_with_vectors.json   # Ready to import (combines 4 files)
    └── MedicalKnowledge_with_vectors.json # Ready to import
```

### Quick Start

1. **Import data using DocumentDB Extension:**
   - Right-click on collections → Import Documents
   - Select the `*_with_vectors.json` files

2. **Create DiskANN vector indexes** (commands in healthcare/README.md)

3. **Run vector search queries** on medical data

**Learn more:** See [healthcare/README.md](healthcare/README.md) for detailed setup instructions and example queries.

---

## Part 6: Performance Tuning (10 minutes)

### Scaling Recommendations

| Vector Count | Recommended Index | Tier | Notes |
|-------------|-------------------|------|-------|
| <10K | IVF | M10/M20 | Fast setup, good for dev |
| 10K-50K | HNSW | M30+ | Best recall, requires RAM |
| 50K-500K | DiskANN | M30+ | Balanced performance |
| 500K+ | DiskANN | M40+ | Enterprise scale |

---

## Troubleshooting

**Slow Queries (>500ms)?**
- ✅ Verify index exists: `db.collection.getIndexes()`
- ✅ Increase cluster tier (M30 → M40)
- ✅ Reduce lSearch value
- ✅ Add filters to narrow search space

**Poor Result Relevance?**
- ✅ Check embedding model consistency (training vs. query)
- ✅ Increase lSearch (try 2-5× current value)
- ✅ Verify similarity metric (COS for text)
- ✅ Inspect embedding dimensions match index

**Index Creation Failed?**
- ✅ DiskANN requires M30+ tier
- ✅ Check vector dimensions are consistent
- ✅ Verify documents have embedding field

---

## Summary

✅ **Vector Search** enables semantic similarity queries beyond keyword matching  
✅ **DiskANN** provides billion-scale search with >95% recall and low memory  
✅ **Filtered Search** combines vectors with business logic (price, location, stock)  
✅ **Integrated Storage** keeps embeddings with source data for simplified architecture

**Key Takeaways:**
- Use DiskANN for 50K+ vectors (disk-efficient, high accuracy)
- Set `lSearch = 4-10× k` for balanced quality/speed
- Combine vector search with filters for production use cases
- Monitor latency and tune maxDegree/lBuild for optimal performance

---

## Next Steps

- **Module 4:** AI Agents with Azure DocumentDB (RAG patterns, LangChain integration)
- **Practice:** Implement vector search for your domain (e-commerce, support tickets, etc.)
- **Explore:** Try HNSW for smaller datasets, compare performance

---

## Resources

**Microsoft Learn:**
- [Vector Search in DocumentDB](https://learn.microsoft.com/en-us/azure/documentdb/vector-search)
- [DiskANN Research Paper](https://www.microsoft.com/en-us/research/publication/diskann-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node/)
- [Product Quantization](https://learn.microsoft.com/en-us/azure/documentdb/product-quantization)

**Sample Code:**
- [Python RAG Examples](https://github.com/microsoft/AzureDataRetrievalAugmentedGenerationSamples/tree/main/Python/CosmosDB-MongoDB-vCore)
- [LangChain Integration](https://python.langchain.com/docs/integrations/vectorstores/azure_cosmos_db/)
