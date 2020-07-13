*******************
API - Utilisation
*******************

Le format de l'URL est toujours le même : *url_machine*/yzi_api/**nom_modele**, suivi de la méthode et ses paramètres.
Le **nom_modele** est le nom technique du modèle dans Odoo.

Si l'on veut rendre certains champs obligatoires ou bien en lecture seule (uniquement pour l'API), il faut se rendre dand le menu *Configuration > API > Paramètres des champs*.

La base de données utilisée doit être définie dans l'*odoo.conf*.

S'authentifier
###############

L'URL à utiliser pour une authentification n'est pas au même format que pour le reste de l'API :
*url_machine*/yzi_api_auth**?login=login&password=password**

Le mot de passe doit être transmis en clair (pour le moment, cela changera dans une prochaine version).

Si les identifiants sont corrects, le cookie *session_id* sera envoyé.
Il faudra l'utiliser dans toutes les requêtes, afin d'être identifié par Odoo.

Chercher
#########

Chercher tout
***************
*/get*

Permet de récupérer tous les enregistrements (actifs) d'une table.

*/get_inactive*

Permet de récupérer tous les enregistrements (inactifs) d'une table.

Chercher par ID
******************
*/get/id*

Permet de récupérer un enregistrement avec son ID.

Chercher par valeur de champs
*******************************
*/search?field=value&field2=value2*

Permet de récupérer des enregistrements selon plusieurs valeurs (city=Valence, par exemple).
Les champs *name* sont insensibles à la casse et la recherche s'effectue avec *contient*.
Il faut utiliser *active=False* pour avoir les enregistrements inactifs. On aura dans ce cas les enregistrements inactifs seulement. Pour avoir les actifs avec, il faut préciser *active=False* ET *active=True*.
Tous les critères s'additionnent avec des *et*.
On peut chercher dans des champs relationnels simples avec un chiffre (l'ID) et dans des champs relationnels multiples avec une liste de chiffres (les IDs).

Créer
#####

*/create?field=value&field2=value2*

Permet de créer un enregistrement.
La création peut être rejetée si un champ obligatoire est manquant, ou bien si un champ est en lecture seule et que l'on essaie d'y mettre une valeur.

Mettre à jour
#############

*/update/id?field=value&field2=value2*

Permet de mettre à jour un enregistrement.
Pour les champs relationnels multiples, les valeurs précédentes sont totalement remplacées par les nouvelles.
La mise à jour peut être rejetée si un champ est en lecture seule et que l'on essaie d'y mettre une valeur.

Supprimer
#########

*/delete/id*

Permet de supprimer un enregistrement.

Appeler une fonction
####################

*/custom?method=method_name&arg=value&arg2=value2*

Permet d'appeler une fonction présente dans le modèle indiqué, avec les paramètres. Il faut obligatoirement le mot clé *method* dans les paramètres pour préciser la méthode à appeler.

*/custom/id?method=method_name&arg=value&arg2=value2*

Permet d'appeler une fonction présente dans le modèle indiqué, avec les paramètres. L'*id* permet d'appeler le bon enregistrement. Il faut obligatoirement le mot clé *method* dans les paramètres pour préciser la méthode à appeler.