****************************
API - Utilisation technique
****************************

Certains fichiers des modules de l'OCA ont été modifiés. S'il faut changer de version ces modules, il faut penser à réappliquer ces modifications.

Le format de l'URL de l'API est défini dans *yzi_api/controllers/main.py*.

On pourra prendre en exemple ce qui existe déjà pour tout ce qui expliqué ci-dessous.

Fonctionnement général
######################

Avant toute tentative de requête, il faut passer par l'authentification, afin d'obtenir un cookie.
Il faut utiliser ce dernier dans toutes les requêtes (ainsi, le *uid* de la session sera rempli).

Quand on entre une URL, on est dirigé sur la méthode associée à la route correspondante.
Celle-ci déclenche un processus de vérification : les paramètres en entrée sont vérifiés, la méthode est exécutée puis la réponse est vérifiée.
On peut sauter ces vérifications avec *@skip_secure_params* et *@skip_secure_response*.

La méthode exécutée est celle du service *abstract*. Ce service ne concerne pas un modèle en particulier. Ainsi, le modèle founit dans l'URL est toujours passé en argument des fonctions.
Dans les arguments, l'ID est également transmis s'il existe. Tous les autres paramètres sont dans un argument \**params (tout ce qui est présent après un *?* dans l'URL).

Ce service *abstract* appelle le modèle *yzi_api_abstract* qui déclenche la méthode dans le modèle précisé, construit les vérificateurs...

Ajouter une route
###################

Dans *base_rest/controllers/main.py*, et dans la classe *RestControllerType*, il faut trouver la méthode *_add_default_methods*.
A la suite des routes déjà présentes, on ajoute la nôtre avec le format :

.. code-block::

        @route([
            '<string:_service_name>',
            '<string:_service_name>/new_method',
            '<string:_service_name>/new_method/<int:_id>',
            ...
        ], methods=['GET' ou 'POST' ou ...])
        def new_method(self, _service_name, _id=None, **params):
            return self._process_method(_service_name, 'new_method', _id, params)

Le *new_method* de **_process_method** doit être le nom de la méthode dans le service *abstract*.
Ne pas oublier d'ajouter les paramètres des routes définies aux arguments de la fonction (*new_method* ici).

Et ne pas oublier d'ajouter à *members* notre fonction :

.. code-block::

        members.update({
            'get': get,
            'get_inactive': get_inactive,
            'search': search,
            'create': create,
            'update': update,
            'delete': delete,
            'custom': custom,
            'new_method': new_method
        })

Vérificateurs
#############

Les vérificateurs permettent de vérifier les paramètres en entrée et ce qui est retourné.
Les méthodes doivent s'appeler _validator_**nom_methode** ou _validator_return_**nom_methode**.

Ces validateurs suivent les normes de la librairie Cerberus.

Pour une création, par exemple, on fournit un dictionnaire avec le nom des champs en clé et leurs caractéristiques dans un dictionnaire en valeur (le type, s'il peut être vide, s'il est obligatoire...)

Pour le retour, on fournit le format de la réponse (par exemple, un dictionnaire avec une chaîne et une liste obligatoires).

YziApiAbstract
################

Ce modèle est appelé par le service *abstract*. C'est lui qui effectue toutes les actions (recherche, suppression, appel de fonctions...).

On y trouve les méthodes principales, les méthodes pour créer les validateurs, pour formater les paramètres si besoin et pour transformer les enregistrements en JSON.

SettingsField
###############

Ce modèle permet de définir, pour l'API, les champs obligatoire ou en lecture seule pour chaque modèle.

IrHttp
#######

Permet de définir l'utilisateur qui envoie la requête, afin de gérer les droits.
On récupère l'*uid* de la session (rempli grâce au cookie) pour le mettre dans la requête.
Cela permet d'indiquer à Odoo qui a envoyé la demande.

Http
################

Contient la méthode d'authentification.

EN DEVELOPPEMENT : MOT DE PASSE EN CLAIR.

AbstractService
#################

C'est le service où sont contenues toutes les méthodes appelées par les routes.

Ce service fait appel au modèle *yzi_api_abtract* et ne fait pas les actions lui-même (il définit simplement le format des réponses).

On y trouve les validateurs, les méthodes et le formatage en JSON.

