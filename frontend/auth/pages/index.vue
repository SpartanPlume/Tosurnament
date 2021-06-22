<template>
  <div id="container">
    <div id="auth-explanation">To authenticate yourself for Tosurnament, please click the button below:</div>
    <button type="button" id="osu-auth" @click="goToOsuAuthorize">Login with osu!</button>
  </div>
</template>

<script>
export default {
  validate({ query }) {
    if (query.code) {
      return true;
    }
    return false;
  },
  methods: {
    goToOsuAuthorize: async function (event) {
      const parameters = {
        client_id: "7694",
        redirect_uri: window.location.origin + "/redirect",
        response_type: "code",
        scope: "identify",
        state: this.$route.query.code
      };
      let url = "https://osu.ppy.sh/oauth/authorize?";
      let parameters_array = [];
      for (const [key, value] of Object.entries(parameters)) {
        parameters_array.push(key + "=" + value);
      }
      url += parameters_array.join("&");
      window.location.href = url;
    }
  }
};
</script>

<style>
html,
body {
  height: 100%;
  width: 100%;
}

body {
  background-color: #1a1c1d;
  margin: 0;
  display: table;
}

#__nuxt {
  height: 100%;
  display: table-row;
}

#__layout {
  height: 100%;
  display: grid;
}

#container {
  margin: auto;
}

#auth-explanation {
  color: #eeeeee;
}

#osu-auth {
  -webkit-touch-callout: none; /* iOS Safari */
  -webkit-user-select: none; /* Safari */
  -khtml-user-select: none; /* Konqueror HTML */
  -moz-user-select: none; /* Old versions of Firefox */
  -ms-user-select: none; /* Internet Explorer/Edge */
  user-select: none;

  display: block;
  margin-top: 10px;
  margin-left: auto;
  margin-right: auto;
  background-color: #ee5f9f;
  border-color: #555555;
  border-radius: 6px;
  color: #ffffff;
  text-align: center;
  font-weight: 700;
  padding: 10px 20px;
  box-shadow: 0 3px #bb4b8e, 0 4px 3px rgba(0, 0, 0, 0.25);
}

#osu-auth:active {
  transform: translateY(1px);
  box-shadow: 0 2px #8a3869, 0 3px 2px rgba(0, 0, 0, 0.25);
  background-color: #ce4f88 !important;
  color: #eeeeee;
}

#osu-auth:hover {
  cursor: pointer;
  background-color: #ff6cae;
}
</style>
