/**
 * Kostra programu pro 2. projekt IZP 2022/23
 *
 * Jednoducha shlukova analyza: 2D nejblizsi soused.
 * Single linkage
 */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h> // sqrtf
#include <limits.h> // INT_MAX

/*****************************************************************
 * Ladici makra. Vypnout jejich efekt lze definici makra
 * NDEBUG, napr.:
 *   a) pri prekladu argumentem prekladaci -DNDEBUG
 *   b) v souboru (na radek pred #include <assert.h>
 *      #define NDEBUG
 */
#ifdef NDEBUG
#define debug(s)
#define dfmt(s, ...)
#define dint(i)
#define dfloat(f)x 
#else

// vypise ladici retezec
#define debug(s) printf("- %s\n", s)

// vypise formatovany ladici vystup - pouziti podobne jako printf
#define dfmt(s, ...) printf(" - "__FILE__":%u: "s"\n",__LINE__,__VA_ARGS__)

// vypise ladici informaci o promenne - pouziti dint(identifikator_promenne)
#define dint(i) printf(" - " __FILE__ ":%u: " #i " = %d\n", __LINE__, i)

// vypise ladici informaci o promenne typu float - pouziti
// dfloat(identifikator_promenne)
#define dfloat(f) printf(" - " __FILE__ ":%u: " #f " = %g\n", __LINE__, f)

#endif

/*****************************************************************
 * Deklarace potrebnych datovych typu:
 *
 * TYTO DEKLARACE NEMENTE
 *
 *   struct obj_t - struktura objektu: identifikator a souradnice
 *   struct cluster_t - shluk objektu:
 *      pocet objektu ve shluku,
 *      kapacita shluku (pocet objektu, pro ktere je rezervovano
 *          misto v poli),
 *      ukazatel na pole shluku.
 */

struct obj_t {
    int id;
    float x;
    float y;
};

struct cluster_t {
    int size;
    int capacity;
    struct obj_t *obj;
};

/*****************************************************************
 * Deklarace potrebnych funkci.
 *
 * PROTOTYPY FUNKCI NEMENTE
 *
 * IMPLEMENTUJTE POUZE FUNKCE NA MISTECH OZNACENYCH 'TODO'
 *
 */

/*
 Inicializace shluku 'c'. Alokuje pamet pro cap objektu (kapacitu).
 Ukazatel NULL u pole objektu znamena kapacitu 0.
*/
void init_cluster(struct cluster_t *c, int cap)
{
    assert(c != NULL);
    assert(cap >= 0);
    if (cap > 0) // Overenie spravnej kapacity
    {
        c->obj = malloc(cap * sizeof(struct obj_t)); // Alokovanie pamate pre cap pocet objektov
        if(c->obj != NULL) // Alokacia prebehla uspene, nastavime hodnoty shluku
        {
            c->capacity = cap;
            c->size = 0;
        } 
        else // Alokacia neprebehla uspesne
        {
            c->capacity = 0;
            fprintf(stderr,"Chyba: Alokacia neprebehla\n");
            return;
        } 
    }
    else if (cap == 0) //Ukazatel NULL u pola objektov znamena kapacitu 0
    {
        c->capacity = cap;
        c->size = 0;
    }   
}

/*
 Odstraneni vsech objektu shluku a inicializace na prazdny shluk.
 */
void clear_cluster(struct cluster_t *c)
{
    free(c->obj); // Uvolnenie alokovanej pamate shluku c
    init_cluster(c, 0); // Inicializacia na prazdny shluk
}

/// Chunk of cluster objects. Value recommended for reallocation.
const int CLUSTER_CHUNK = 10;

/*
 Zmena kapacity shluku 'c' na kapacitu 'new_cap'.
 */
struct cluster_t *resize_cluster(struct cluster_t *c, int new_cap)
{
    // TUTO FUNKCI NEMENTE
    assert(c);
    assert(c->capacity >= 0);
    assert(new_cap >= 0);
    if (c->capacity >= new_cap)
        return c;

    size_t size = sizeof(struct obj_t) * new_cap;

    void *arr = realloc(c->obj, size);
    if (arr == NULL)
        return NULL;

    c->obj = (struct obj_t*)arr;
    c->capacity = new_cap;
    return c;
}

/*
 Prida objekt 'obj' na konec shluku 'c'. Rozsiri shluk, pokud se do nej objekt
 nevejde.
 */
void append_cluster(struct cluster_t *c, struct obj_t obj)
{
    if(c->size == c->capacity) // Objekt sa uz nevojde
    {
        c = resize_cluster(c, c->capacity + CLUSTER_CHUNK); // Rozsirenie shluku
        if (c == NULL) // Overenie alokacie
        {
            fprintf(stderr,"Chyba: Alokacia shluku neprebehla\n");
            return;
        }   
    }
    if (c->size < c->capacity) // Objekt sa vojde
    {
        c->obj[c->size] = obj; // Pridanie objektu do pola
        c->size+=1; // Pripocitanie objektu
    }   
}

/*
 Seradi objekty ve shluku 'c' vzestupne podle jejich identifikacniho cisla.
 */
void sort_cluster(struct cluster_t *c);

/*
 Do shluku 'c1' prida objekty 'c2'. Shluk 'c1' bude v pripade nutnosti rozsiren.
 Objekty ve shluku 'c1' budou serazeny vzestupne podle identifikacniho cisla.
 Shluk 'c2' bude nezmenen.
 */
void merge_clusters(struct cluster_t *c1, struct cluster_t *c2)
{
    assert(c1 != NULL);
    assert(c2 != NULL);
    for (int i = 0; i < c2->size; i++) // Pridavanie vsetkych objektov shluku c2
    {
        append_cluster(c1, c2->obj[i]);
    }
    sort_cluster(c1); // Zoradenie objektov shluku c1 podla ident. cisla
    
}

/**********************************************************************/
/* Prace s polem shluku */

/*
 Odstrani shluk z pole shluku 'carr'. Pole shluku obsahuje 'narr' polozek
 (shluku). Shluk pro odstraneni se nachazi na indexu 'idx'. Funkce vraci novy
 pocet shluku v poli.
*/
int remove_cluster(struct cluster_t *carr, int narr, int idx)
{
    assert(idx < narr);
    assert(narr > 0);
    clear_cluster(&carr[idx]); // Odstranenie shluku
    for (int i = idx; i < narr - 1; i++)
    {
        carr[i] = carr[i+1]; // Zmensenie pola po odstraneni shluku
    }
    return narr - 1; // Novy pocet shlukov
}

/*
 Pocita Euklidovskou vzdalenost mezi dvema objekty.
 */
float obj_distance(struct obj_t *o1, struct obj_t *o2)
{
    assert(o1 != NULL);
    assert(o2 != NULL);
    // Vypocet Euklidovskej vzdalenosti z wikipedie
    return sqrtf( ((o1->x - o2->x) * (o1->x-o2->x)) + ((o1->y - o2->y) * (o1->y - o2->y)));
}

/*
 Pocita vzdalenost dvou shluku.
*/
float cluster_distance(struct cluster_t *c1, struct cluster_t *c2)
{
    assert(c1 != NULL);
    assert(c1->size > 0);
    assert(c2 != NULL);
    assert(c2->size > 0);
    int min = 1000 * sqrt(2); // Najvacsia mozna vzdialenost 2 objektov
    for (int i = 0; i < c1->size; i++) // Porovnavanie kazdy s kazdym
    {
        for (int j = 0; j < c2->size; j++)
        {
            int curr = obj_distance(&(c1->obj[i]), &(c2->obj[j])); //Terajsia vzdialenost 2 objektov
            if (curr < min) // Ak je mensia ako min, prepise ho
            {
                min = curr;
            }
        }  
    }
    return min; // Vracia najmensiu vzdialenost
}

/*
 Funkce najde dva nejblizsi shluky. V poli shluku 'carr' o velikosti 'narr'
 hleda dva nejblizsi shluky. Nalezene shluky identifikuje jejich indexy v poli
 'carr'. Funkce nalezene shluky (indexy do pole 'carr') uklada do pameti na
 adresu 'c1' resp. 'c2'.
*/
void find_neighbours(struct cluster_t *carr, int narr, int *c1, int *c2)
{
    assert(narr > 0);
    int min = 1000 * sqrt(2); // Najvacsia mozna vzdialenost 2 shlukov
    for (int i = 0; i < narr; i++) // Porovnavanie kazdy s kazdym
    {
        for (int j = 0; j < narr; j++)
        {
            if(i == j) // Porovnanie shluku so sebou samym
            {
                continue;
            }
            int curr = cluster_distance(&(carr[i]), &(carr[j])); //Terajsia vzdialenost 2 shlukov
            if (curr < min) // Ak je mensia ako min, prepise ho, najdene shluky ulozime
            {
                min = curr;
                *c1 = i;
                *c2 = j;
            }
        }
    }
}

// pomocna funkce pro razeni shluku
static int obj_sort_compar(const void *a, const void *b)
{
    // TUTO FUNKCI NEMENTE
    const struct obj_t *o1 = (const struct obj_t *)a;
    const struct obj_t *o2 = (const struct obj_t *)b;
    if (o1->id < o2->id) return -1;
    if (o1->id > o2->id) return 1;
    return 0;
}

/*
 Razeni objektu ve shluku vzestupne podle jejich identifikatoru.
*/
void sort_cluster(struct cluster_t *c)
{
    // TUTO FUNKCI NEMENTE
    qsort(c->obj, c->size, sizeof(struct obj_t), &obj_sort_compar);
}

/*
 Tisk shluku 'c' na stdout.
*/
void print_cluster(struct cluster_t *c)
{
    // TUTO FUNKCI NEMENTE
    for (int i = 0; i < c->size; i++)
    {
        if (i) putchar(' ');
        printf("%d[%g,%g]", c->obj[i].id, c->obj[i].x, c->obj[i].y);
    }
    putchar('\n');
}

/*
 Ze souboru 'filename' nacte objekty. Pro kazdy objekt vytvori shluk a ulozi
 jej do pole shluku. Alokuje prostor pro pole vsech shluku a ukazatel na prvni
 polozku pole (ukalazatel na prvni shluk v alokovanem poli) ulozi do pameti,
 kam se odkazuje parametr 'arr'. Funkce vraci pocet nactenych objektu (shluku).
 V pripade nejake chyby uklada do pameti, kam se odkazuje 'arr', hodnotu NULL.
*/
int load_clusters(char *filename, struct cluster_t **arr)
{
    assert(arr != NULL);
    int rHod = 0; // hodnota return
    int count; // hodnota count
    FILE* subor = fopen(filename, "r"); // Otvorenie suboru (Iba na citanie)
    if (subor == NULL) // Neuspesne otvorenie suboru
    {
       fprintf(stderr,"Chyba: Subor sa nepodarilo otvorit\n");
       return 0; 
    }
    fscanf(subor, "count=%d\n", &count); // Zistenie poctu objektov zo suboru
    *arr = malloc(count*sizeof(struct cluster_t)); // Alokovanie pamate pre pole shlukov
    struct obj_t newO; // vytvorenie objektu
    for (int i = 0; i < count; i++)
    {
        if (fscanf(subor, "%d %f %f", &newO.id, &newO.x, &newO.y) == 3) // Nacitanie parametrov objektu zo suboru
        {
            if ((newO.x<=1000 && newO.x>=0) && (newO.y<=1000 && newO.y>=0)) // Kontrola spravnych suradnic objektu
            {
                char c = fgetc(subor); // Premenna pre 4. parameter objektu
                if (c == EOF || c == '\n') // Ak sa rovna, ulozi objekt do shluku
                {
                    init_cluster(&(*arr)[i], CLUSTER_CHUNK); // Inicializacia noveho shluku
                    append_cluster((*arr + i), newO); // Pridanie objektu do shluku
                    rHod = i + 1;
                }
                else
                {
                    fprintf(stderr,"Chyba: Nespravny pocet hodnot\n");
                    return 0;
                }
            }
            else
            {
                fprintf(stderr,"Chyba: Nespravna velkost x/y hodnoty\n");
                return 0;
            }
        }  
    }
    if (fclose(subor) == EOF) // Neuspesne zavretie suboru
    {
        fprintf(stderr,"Chyba: Subor sa nepodarilo zavriet\n");
        return 0;
    }
    return rHod; // Hodnota nacitanych objektov (shlukov)
}

/*
 Tisk pole shluku. Parametr 'carr' je ukazatel na prvni polozku (shluk).
 Tiskne se prvnich 'narr' shluku.
*/
void print_clusters(struct cluster_t *carr, int narr)
{
    printf("Clusters:\n");
    for (int i = 0; i < narr; i++)
    {
        printf("cluster %d: ", i);
        print_cluster(&carr[i]);
    }
}

int main(int argc, char *argv[])
{ 
    struct cluster_t *clusters;
    int ClusterLoadCount = load_clusters(argv[1], &clusters); // Nacitanie a zistenie poctu objektov zo suboru
    if (argc == 3) // Ak ma 3 parametre (./cluster subor N)
    {
        int ClusterInsertCount = atoi(argv[2]); // Zistenie poctu shlukov z parametru N
        while (ClusterLoadCount > ClusterInsertCount)
        {
            int c1, c2;
            find_neighbours(clusters, ClusterLoadCount, &c1, &c2);
            merge_clusters(&clusters[c1], &clusters[c2]);
            ClusterLoadCount = remove_cluster(clusters, ClusterLoadCount, c2); 
        }
        if (ClusterInsertCount > ClusterLoadCount) // Overenie ci je parameter N mensi ako pocet objektov v subore
        {
            fprintf(stderr,"Chyba: Nespravna hodnota parametru\n");
            return 1;
        }
    }
    else if (argc > 3) // Viac ako 3 parametre
    {
        fprintf(stderr,"Chyba: Nespravny pocet zadanych parametrov N\n");
        return 1;
    }
    print_clusters(clusters, ClusterLoadCount); // Vypise shluky
    for (int i = 0; i < ClusterLoadCount;) // Postupne uvolnovanie alokovanej pamati objektov
    {
        ClusterLoadCount = remove_cluster(clusters, ClusterLoadCount, 0); // ClusterLoadCount sa postupne mensi (az do 0)
    }
    free(clusters); // Uvolnenie alokovanej pamati objektov
    return 0;
}