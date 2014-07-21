import requests as req
from pyshock.exceptions import ApiException
from pyshock.enums import UserLookupType, BanLookupType
from urllib.parse import urljoin, urlencode

class TShock():
    """The main API wrapper. This class handles all requests.
    The functions in this class document what endpoint they belong to
    and have names that describe their functions.

    All of the functions beginning with ``get_`` do not edit any server values.
    ``get_`` functions simply query the TShock server using any of the REST endpoints
    that do not update, create, or delete data. An example is returning a list of players.
    Of CRUD, ``get_`` covers Read.

    All of the functions beginning with ``set_`` will edit some sort of value on the server's end.
    ``set_`` functions are used to update, create, or delete data. An example is banning a player.
    Of CRUD, ``set_`` covers Update.

    All of the functions beginning with ``do_`` will perform some sort of action that
    will edit the TShock server's state somehow, but will not cause permanent changes.
    These are typically actions taken somehow. An example is butchering all NPCs.
    Of CRUD, ``do_`` covers Create and Delete.

    All of the functions will return a dict. The dict is a mapping of the JSON data
    returned by the TShock server as a REST response. Every response will contain the
    ``status`` member. The ``status`` member is the HTTP status code that the TShock server
    returned. Any statuses other than 200 and 400 will not be returned and will instead
    be thrown as ApiExceptions. Most of the mappings returned will have a ``response``
    member. This indicates success or failure and the best way to find out what
    the mapping will contain would be to consult the REST API source or documentation.

    After instantiation, the :py:meth:`get_token` function should be run to obtain a token
    corresponding to a specific user. All requests will pass the token. You cannot
    make most requests without a token.

    Your user is required to have the appropriate permission assigned to them by the TShock
    server for some requests. These permissions are not documented here and may be found in the
    TShock RESTful API documenation:
    https://tshock.atlassian.net/wiki/display/TSHOCKPLUGINS/REST+API+Endpoints#RESTAPIEndpoints-/v2/users/activelist

    Example usage of the API:

    >>> tshock = pyshock.TShock()
    >>> tshock.get_token("Ijwu","test")
    >>> tshock.get_active_user_list()
    {'status': '200', 'activeusers': 'Ijwu'}

    :param str ip:
        the ip address of the TShock server

    :param int port:
        the port that the REST API is opened on
    """
    def __init__(self, ip, port):
        self.urls = RequestBuilder(ip, port)
        self.ip = ip
        self.port = port
        self.token = ""

    def _make_request(self, url : str) -> dict:
        """Makes a GET request to the specified url.
        Takes care of checking the response status as well
        as handling all possible connection errors.

        :param str url:
            Url string to make a GET request to.

        :returns:
            A dict mapping of the json reply.
            every response dict has a ``status`` member
            indicating the HTTP response status. MOst mappings
            have a ``response`` member.

        :raises ApiException:
            If the request times out or the REST response returns a status other than 200 or 400.
        """
        try:
            res = req.get(url)
        except Exception:
            raise ApiException("An error occurred in making the request to the server.")
        results = res.json()
        if results['status'] == "404":
            raise ApiException("404 Error. Are you sure the server has REST enabled?")
        elif results['status'] in ["200", "400"]:
            pass
        else:
            raise ApiException("Error in request. Server returned status: {0} With error: {1}".format(
                results["status"],
                results["error"]
            ))
        return results

    def get_token(self, user : str, password : str):
        """Gets and stores a token for the user.
        The token is used for all rest endpoints that require authentication.
        The token may be overridden by running this function again.

        :param str user:
            String representing the user to obtain the token under.

        :param str password:
            String that is the user's password.

        **endpoint:** v2/token/create/
        """
        self.urls.token = self._make_request(
            self.urls.get_url("v2", "token", "create", password, username=user)
        )["token"]

    def get_status(self) -> dict:
        """Gets the server status.

        :returns:
            A dict with these items:
                * name - Server name
                * port - Server port
                * playercount - Amount of players on the server
                * players - CSV list of players currently connected

        **endpoint:** /status
        """
        return self._make_request(self.urls.get_url("status"))

    def get_token_status(self) -> bool:
        """Tests if the the currently saved token is still valid.

        :returns:
            True if the token is valid. False otherwise.

        **endpoint:** /tokentest
        """
        try:
            self._make_request(self.urls.get_url("tokentest"))
        except ApiException:
            return False
        return True

    def get_server_status_v2(self, players=False, rules=False, filters=None) -> dict:
        """Gets the server status. Includes various items based
        on the parameters sent.

        :param bool players:
            Bool deciding if players should be included in the response.

        :param bool rules:
            Bool deciding if server config rules should be included in the response.

        :param dict filters:
            Dict of filters to be applied to the player search. May contain these items:
                * nickname
                * username
                * group
                * active
                * state
                * team

        :returns:
            A dict with these items:
                * name - Server name
                * port - Port the server is running on
                * playercount - Number of players currently online
                * maxplayers - The maximum number of players the server support
                * world - The name of the currently running world
                * players - (optional) an array of players including the following information:
                    * nickname
                    * username
                    * ip
                    * group
                    * active
                    * state
                    * team
                * rules - (optional) an array of server rules which are name value pairs e.g. AutoSave, DisableBuild etc

        **endpoint:** /v2/server/status
        """
        if filters is None:
            filters = {}
        return self._make_request(self.urls.get_url("v2", "server", "status", players=players, rules=rules, **filters))

    def get_active_user_list(self):
        """Gets the currently active players logged into a server.

        :returns:
            A dict with these items:
                * activeusers - list of active users

        **endpoint:** /v2/users/activelist
        """
        return self._make_request(self.urls.get_url("v2", "users", "activelist"))

    def get_user_info(self, lookup : UserLookupType, user : str):
        """Gets information about a specific user.

        :param UserLookupType lookup:
            Should be a value of the UserLookupType Enum stating what the
            lookup value is.

        :param str user:
            String that is either the user name, id, or ip, depending on the
            lookup type.

        :returns:
            A dict with these items:
                * group - The group the user belong's to
                * id - The user's ID
                * name - The name of the user
                * ip - The ip of the user

        **endpoint:** /v2/users/read
        """
        return self._make_request(self.urls.get_url("v2", "users", "read", type=lookup.value, user=user))

    def get_ban_information(self, lookup : BanLookupType, user : str) -> dict:
        """Gets information about a ban.

        :param BanLookupType lookup:
            a BanLookupType value dictating how to search
            for the user

        :param str user:
            the user info to search for

        :returns:
            a dict with these items:
                * name - The username of the player
                * ip - The IP address of the player
                * reason - The reason the player was banned

        **endpoint:** /v2/bans/read
        """
        return self._make_request(self.urls.get_url("v2", "bans", "read", type=lookup.value, ban=user))

    def get_ban_list(self):
        """Gets a list of all of the bans on the server.

        :returns:
            A dict with these items:
                * bans - An array of all the currently banned players including:
                    * name
                    * ip
                    * reason

        **endpoint:** /v2/bans/list
        """
        return self._make_request(self.urls.get_url("v2", "bans", "list"))

    def get_player_list(self):
        """Gets a list of all of the players currently on the server.

        :returns:
            A dict with these items:
                * players - A list of all current players on the server, separated by a comma.

        **endpoint:** /v2/players/list
        """
        return self._make_request(self.urls.get_url("v2", "players", "list"))

    def get_player_info(self, player : str):
        """Gets information about a specific player.

        :param str player:
            The player to look for, by name.

        :returns:
            A dict with these items:
                * nickname - The player's nickname
                * username - The player's username (if they are registered)
                * ip - The player's IP address
                * group - The group that the player belongs to
                * position - The player's current position on the map
                * inventory - A list of all items in the player's inventory
                * buffs - A list of all buffs that are currently affecting the player

        **endpoint:** /v2/players/read
        """
        return self._make_request(self.urls.get_url("v2", "players", "read", player=player))

    def get_world_info(self):
        """Gets some information about the current world.

        :returns:
            A dict with these items:
                * name - The world name
                * size - The dimensions of the world
                * time - The current time in the world
                * daytime - Bool value indicating whether it is daytime or not
                * bloodmoon - Bool value indicating whether there is a blood moon or not
                * invasionsize - The current invasion size

        **endpoint:** /world/read
        """
        return self._make_request(self.urls.get_url("world", "read"))

    def get_group_list(self):
        """Returns a list of all of the groups on the server.

        :returns:
            A dict with these items:
                * groups - An array of the groups configured on the server including:
                    * name
                    * parent
                    * chatcolor

        **endpoint:** /v2/groups/list
        """
        return self._make_request(self.urls.get_url("v2", "groups", "list"))

    def get_group_info(self, group : str):
        """Returns info about a specific group.

        :param str group:
            The group to search for.

        :returns:
            A dict with these items:
                * name - The name of the group
                * parent - The name of the parent of this group
                * chatcolor - The chat color of this group
                * permissions - An array of permissions assigned "directly" to this group
                * negatedpermissions - An array of negated permissions assigned "directly" to this group
                * totalpermissions - An array of the calculated permissions available to members of this group
                                     due to direct permissions and inherited permissions

        **endpoint:** /v2/groups/read
        """
        return self._make_request(self.urls.get_url("v2", "groups", "read", group=group))

    def get_server_motd(self):
        """Gets the server's MOTD.

        :returns:
            A dict with these items:
                * motd - The server's Message of the Day

        **endpoint:** /v3/server/motd
        """
        return self._make_request(self.urls.get_url("v3", "server", "motd"))

    def get_server_rules(self):
        """Gets the server's rules.

        :returns:
            A dict with these items:
                * rules - The server rules

        **endpoint:** /v3/server/rules
        """
        return self._make_request(self.urls.get_url("v3", "server", "rules"))

    def do_destroy_token(self):
        """Destroys the token being used by this class.

        **endpoint:** /token/destroy
        """
        self._make_request(self.urls.get_url("token", "destroy", self.urls.token))

    def do_destroy_all_tokens(self):
        """Destroys all tokens registered with the server.

        **endpoint:** /v3/token/destroy/all
        """
        self._make_request(self.urls.get_url("v3", "token", "destroy", "all"))

    def do_server_broadcast(self, message : str):
        """Broadcasts a message to all users on the server.

        :param str message:
            The message to be broadcasted.

        **endpoint:** /v2/server/broadcast
        """
        self._make_request(self.urls.get_url("v2", "server", "broadcast", msg=message))

    def do_server_reload(self):
        """Reloads the config file, permissions, and regions of the server.

        **endpoint:** /v3/server/reload
        """
        self._make_request(self.urls.get_url("v3", "server", "reload"))

    def do_server_off(self):
        """Shuts down the server.

        **endpoint:** /v2/server/off
        """
        self._make_request(self.urls.get_url("v2", "server", "off"))

    def do_server_restart(self):
        """Restarts the server.

        **endpoint:** /v3/server/restart
        """
        self._make_request(self.urls.get_url("v3", "server", "restart"))

    def do_server_rawcmd_v2(self, command : str):
        """Executes a command on the server and returns the output.

        :param str command:
            The command to be executed.

        :returns:
            A dict with these items:
                * response - The output of the command as a string. Each line of output is separated by a newline.

        **endpoint:** /v2/server/rawcmd
        """
        return self._make_request(self.urls.get_url("v2", "server", "rawcmd", cmd=command))

    def do_server_rawcmd_v3(self, command : str):
        """Executes a command on the server and returns the output.

        :param str command:
            The command to be executed.

        :returns:
            A dict with these items:
                * response - The output of the command as an array of strings.

        **endpoint:** /v3/server/rawcmd
        """
        return self._make_request(self.urls.get_url("v3", "server", "rawcmd", cmd=command))

    def do_create_ban(self, ip : str, name : str, reason : str):
        """Bans a user.

        :param str ip:
            The ip address to ban. Is required.

        :param str name:
            The player name to ban. May be an empty string.

        :param str reason:
            The reason the player was banned. May be an empty string.

        **endpoint:** /bans/create
        """
        self._make_request(self.urls.get_url("bans", "create", ip=ip, name=name, reason=reason))

    def do_delete_ban(self, type : BanLookupType, ban : str):
        """Deletes a ban.

        :param BanLookupType type:
            Defines how to search for the ban to be deleted.

        :param str ban:
            The ban to delete.

        **endpoint:** /v2/bans/destroy
        """
        self._make_request(self.urls.get_url("v2", "bans", "destroy", ban=ban, type=type))

    def do_world_meteor(self):
        """Drops a meteor on the world.

        **endpoint:** /world/meteor
        """
        self._make_request(self.urls.get_url("world", "meteor"))

    def do_world_save(self):
        """Saves the world. (No, not like Superman.)

        **endpoint:** /v2/world/save
        """
        self._make_request(self.urls.get_url("v2", "world", "save"))

    def do_world_butcher(self, killFriendly : bool):
        """Butchers all NPCs. Will never kill town NPCs, even if killFriendly
        is enabled.

        :param bool killFriendly:
            Whether to kill friendly mobs or not, such as bunnies.

        **endpoint:** /v2/world/butcher
        """
        self._make_request(self.urls.get_url("v2", "world", "butcher", killfriendly=killFriendly))

    def do_kick_player(self, player : str, reason : str):
        """Kicks a player.

        :param str reason:
            The reason the player was kicked.

        **endpoint:** /v2/players/kick
        """
        self._make_request(self.urls.get_url("v2", "players", "kick", reason=reason, player=player))

    def do_ban_player(self, player : str, reason : str):
        """Bans a player permanently.

        :param str player:
            Player to be banned.

        :param reason:
            Reason for the ban.

        **endpoint:** /v2/players/ban
        """
        self._make_request(self.urls.get_url("v2", "players", "ban", reason=reason, player=player))

    def do_kill_player(self, player : str, killer : str):
        """Kills a player.

        :param player:
            Player to be killed.

        :param killer:
            Person who 'killed' the player. This is displayed as "{killer} just killed you!"
            to the player.

        **endpoint:** /v2/players/kill
        """
        self._make_request(self.urls.get_url("v2", "players", "kill", player=player, **{"from":killer}))

    def do_mute_player(self, player : str):
        """Mutes a player.

        :param str player:
            Player to be muted.

        **endpoint:** /v2/players/mute
        """
        self._make_request(self.urls.get_url("v2", "players", "mute", player=player))

    def do_unmute_player(self, player : str):
        """Unmutes a player.

        :param str player:
            Player to be unmuted.

        **endpoint:** /v2/players/unmute
        """
        self._make_request(self.urls.get_url("v2", "players", "unmute", player=player))

    def do_group_delete(self, group : str):
        """Deletes a group.

        :param str group:
            The group to be deleted.

        **endpoint:** /v2/groups/destroy
        """
        self._make_request(self.urls.get_url("v2", "groups", "destroy", group=group))

    def do_group_create(self, group : str, parent : str = "", permissions : str = "", chatColor : str = "255,255,255"):
        """Adds a new group. Includes specification of parent, permissions, and chat color.

        :param str group:
            The name of the group to be created.

        :param str parent:
            The parent of the group to be created.

        :param str permissions:
            The permissions that the group should have as CSV.

        :param str chatColor:
            The group's chat color as three CSV RGB byte values.

        **endpoint:** /v2/groups/create
        """
        self._make_request(self.urls.get_url("v2", "groups", "create",
                                             group=group,
                                             parent=parent,
                                             permissions=permissions,
                                             chatcolor=chatColor))

    def set_update_user(self, user : str, type : UserLookupType, password : str, group : str):
        """Updates a user in the TShock DB.

        :param str user:
            The search string, depending on the the lookup type.

        :param UserLookupType type:
            The method in which to lookup the user.

        :param str password:
            The new password for the user.

        :param str group:
            The new group for the user.

        **endpoint:** /v2/users/update
        """
        self._make_request(self.urls.get_url("v2", "users", "update",
                                             user=user,
                                             type=type.value,
                                             password=password,
                                             group=group))

    def set_world_bloodmoon(self, bloodmoon : bool):
        """Sets the world's bloodmoon.

        :param bool bloodmoon:
            Bool indicating what to set the bloodmoon to.

        **endpoint:** /world/bloodmoon/{bool}
        """
        self._make_request(self.urls.get_url("world", "bloodmoon", bloodmoon))

    def set_world_autosaving(self, autosave : bool):
        """Turns autosaving on or off.

        :param bool autosave:
            Bool indicating whether to turn autosaving on or off.

        **endpoint:** /v2/world/autosave/state/{bool}
        """
        self._make_request(self.urls.get_url("v2", "world", "autosave", "state", autosave))

    def set_group_update(self, group : str, parent : str = None, chatcolor : str = None, permissions : str = None):
        """Updates a group in the TShock DB.

        :param str group:
            The group to be updated.

        :param str parent:
            (Optional) The new parent of the group.

        :param str chatcolor:
            (Optional) The new group chatcolor as CSV RGB byte values.

        :param str permissions:
            (Optional) The new group permissions as a CSV string.

        **endpoint:** /v2/groups/update
        """
        if parent is None:
            parent = ""
        if chatcolor is None:
            chatcolor = ""
        if permissions is None:
            permissions = ""
        self._make_request(self.urls.get_url("v2", "groups", "update",
                                             group=group,
                                             parent=parent,
                                             chatcolor=chatcolor,
                                             permissions=permissions))

class RequestBuilder():
    def __init__(self, ip, post):
        self.ip = ip
        self.post = post
        self.token = ""

    def get_url(self, *args, **kwargs) -> str:
        base = "http://{0}:{1}".format(self.ip, self.post)
        path = "/" + "/".join(args)
        kwargs['token'] = self.token

        params = urlencode(kwargs)
        return "{0}?{1}".format(urljoin(base, path), params)