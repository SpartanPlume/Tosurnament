import Router from "next/router";
import axios from "axios";
import Cookies from "js-cookie";
import { toast } from "react-toastify";

function redirectToLoginIfNeeded(error) {
  if (error.response?.status === 401) {
    Cookies.remove("session_token", { path: "/" });
    Router.push(`/login?redirect=${Router.asPath}`);
  }
}

export default class TosurnamentApi {
  static baseApiPath = "http://localhost:5001/api/v1";

  static async doMethod(method, uri, body = null) {
    const sessionToken = Cookies.get("session_token");
    return await axios({
      method: method,
      url: this.baseApiPath + uri,
      headers: { Authorization: sessionToken },
      data: body
    });
  }

  static async doMethodAndCatchError(method, uri, body = null) {
    try {
      return await TosurnamentApi.doMethod(method, uri, body);
    } catch (e) {
      if (e.response?.data?.detail) {
        toast.error(`${e.response.data.detail}`);
      } else {
        toast.error("Unknown error, please retry");
      }
      redirectToLoginIfNeeded(e);
      throw e;
    }
  }

  static async get(uri) {
    try {
      return await this.doMethod("get", uri);
    } catch (e) {
      redirectToLoginIfNeeded(e);
      throw e;
    }
  }

  static async post(uri, body) {
    return await this.doMethodAndCatchError("post", uri, body);
  }

  static async put(uri, body) {
    return await this.doMethodAndCatchError("put", uri, body);
  }

  static async delete(uri) {
    return await this.doMethodAndCatchError("delete", uri);
  }
}

export function queryMe() {
  return {
    queryKey: "me",
    queryFn: async () => {
      let { data } = await TosurnamentApi.doMethod("get", "/discord/users/me");
      return data;
    }
  };
}

export function queryCommonGuilds() {
  return {
    queryKey: "common_guilds",
    queryFn: async () => {
      let { data } = await TosurnamentApi.get("/discord/guilds/common");
      if (data && "guilds" in data) {
        data = data["guilds"];
      }
      return data;
    }
  };
}

export function queryGuildFromDiscordGuildId(guildId) {
  return {
    queryKey: ["guild", { guild_id: guildId }],
    queryFn: async () => {
      if (!guildId) {
        return null;
      }
      let { data } = await TosurnamentApi.get(`/tosurnament/guilds?guild_id=${guildId}`);
      if (data && "guilds" in data) {
        data = data["guilds"][0];
      }
      return data;
    }
  };
}

export function queryTournamentFromDiscordGuildId(guildId) {
  return {
    queryKey: ["tournament", { guild_id: guildId }],
    queryFn: async () => {
      if (!guildId) {
        return null;
      }
      let { data } = await TosurnamentApi.get(
        `/tosurnament/tournaments?guild_id=${guildId}&include_brackets=true&include_spreadsheets=true`
      );
      if (data && "tournaments" in data) {
        data = data["tournaments"][0];
      }
      return data;
    }
  };
}

export function queryDiscordRoles(guildId) {
  return {
    queryKey: ["roles", { guild_id: guildId }],
    queryFn: async () => {
      if (!guildId) {
        return null;
      }
      let { data } = await TosurnamentApi.get(`/discord/guilds/${guildId}/roles`);
      if (data && "roles" in data) {
        data = data["roles"];
      }
      return data;
    }
  };
}

export function queryDiscordChannels(guildId) {
  return {
    queryKey: ["channels", { guild_id: guildId }],
    queryFn: async () => {
      if (!guildId) {
        return null;
      }
      let { data } = await TosurnamentApi.get(`/discord/guilds/${guildId}/channels`);
      if (data && "channels" in data) {
        data = data["channels"];
      }
      return data;
    }
  };
}
