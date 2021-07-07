<template>
  <div v-if="$fetchState.pending" id="container">
    <div class="sk-circle">
      <div class="sk-circle1 sk-child" />
      <div class="sk-circle2 sk-child" />
      <div class="sk-circle3 sk-child" />
      <div class="sk-circle4 sk-child" />
      <div class="sk-circle5 sk-child" />
      <div class="sk-circle6 sk-child" />
      <div class="sk-circle7 sk-child" />
      <div class="sk-circle8 sk-child" />
      <div class="sk-circle9 sk-child" />
      <div class="sk-circle10 sk-child" />
      <div class="sk-circle11 sk-child" />
      <div class="sk-circle12 sk-child" />
    </div>
    <p>Linking your discord account with your osu! account...</p>
  </div>
  <div v-else-if="$fetchState.error" id="container">
    <img src="~assets/images/cancel_black_48dp.svg" />
    <p>Error while linking your account, please retry.</p>
  </div>
  <div v-else id="container">
    <img src="~assets/images/check_circle_black_48dp.svg" />
    <p>Your discord account has successfully been linked to your osu! account.</p>
  </div>
</template>

<script>
export default {
  validate({ query }) {
    if (query.code && query.state) {
      return true;
    }
    return false;
  },
  fetchOnServer: true,
  async fetch() {
    const query = this.$nuxt.context.query;
    const code = query.code;
    const oauth_token_url = "http://localhost:5001/auth";
    const parameters = {
      tosurnament_code: query.state,
      osu_code: code
    };
    let result = await fetch(oauth_token_url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(parameters)
    });
    if (!result.ok) {
      throw new Error();
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

img {
  margin: auto;
  display: block;
  width: 10%;
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
  width: 50%;
}

p {
  font-size: 32px;
  color: #eeeeee;
  text-align: center;
}

@media only screen and (max-width: 768px) {
  p {
    font-size: 16px;
  }
}

.sk-circle {
  margin: auto;
  width: 40px;
  height: 40px;
  position: relative;
}
.sk-circle .sk-child {
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
}
.sk-circle .sk-child:before {
  content: "";
  display: block;
  margin: 0 auto;
  width: 15%;
  height: 15%;
  background-color: #aaa;
  border-radius: 100%;
  -webkit-animation: sk-circleBounceDelay 1.2s infinite ease-in-out both;
  animation: sk-circleBounceDelay 1.2s infinite ease-in-out both;
}
.sk-circle .sk-circle2 {
  -webkit-transform: rotate(30deg);
  -ms-transform: rotate(30deg);
  transform: rotate(30deg);
}
.sk-circle .sk-circle3 {
  -webkit-transform: rotate(60deg);
  -ms-transform: rotate(60deg);
  transform: rotate(60deg);
}
.sk-circle .sk-circle4 {
  -webkit-transform: rotate(90deg);
  -ms-transform: rotate(90deg);
  transform: rotate(90deg);
}
.sk-circle .sk-circle5 {
  -webkit-transform: rotate(120deg);
  -ms-transform: rotate(120deg);
  transform: rotate(120deg);
}
.sk-circle .sk-circle6 {
  -webkit-transform: rotate(150deg);
  -ms-transform: rotate(150deg);
  transform: rotate(150deg);
}
.sk-circle .sk-circle7 {
  -webkit-transform: rotate(180deg);
  -ms-transform: rotate(180deg);
  transform: rotate(180deg);
}
.sk-circle .sk-circle8 {
  -webkit-transform: rotate(210deg);
  -ms-transform: rotate(210deg);
  transform: rotate(210deg);
}
.sk-circle .sk-circle9 {
  -webkit-transform: rotate(240deg);
  -ms-transform: rotate(240deg);
  transform: rotate(240deg);
}
.sk-circle .sk-circle10 {
  -webkit-transform: rotate(270deg);
  -ms-transform: rotate(270deg);
  transform: rotate(270deg);
}
.sk-circle .sk-circle11 {
  -webkit-transform: rotate(300deg);
  -ms-transform: rotate(300deg);
  transform: rotate(300deg);
}
.sk-circle .sk-circle12 {
  -webkit-transform: rotate(330deg);
  -ms-transform: rotate(330deg);
  transform: rotate(330deg);
}
.sk-circle .sk-circle2:before {
  -webkit-animation-delay: -1.1s;
  animation-delay: -1.1s;
}
.sk-circle .sk-circle3:before {
  -webkit-animation-delay: -1s;
  animation-delay: -1s;
}
.sk-circle .sk-circle4:before {
  -webkit-animation-delay: -0.9s;
  animation-delay: -0.9s;
}
.sk-circle .sk-circle5:before {
  -webkit-animation-delay: -0.8s;
  animation-delay: -0.8s;
}
.sk-circle .sk-circle6:before {
  -webkit-animation-delay: -0.7s;
  animation-delay: -0.7s;
}
.sk-circle .sk-circle7:before {
  -webkit-animation-delay: -0.6s;
  animation-delay: -0.6s;
}
.sk-circle .sk-circle8:before {
  -webkit-animation-delay: -0.5s;
  animation-delay: -0.5s;
}
.sk-circle .sk-circle9:before {
  -webkit-animation-delay: -0.4s;
  animation-delay: -0.4s;
}
.sk-circle .sk-circle10:before {
  -webkit-animation-delay: -0.3s;
  animation-delay: -0.3s;
}
.sk-circle .sk-circle11:before {
  -webkit-animation-delay: -0.2s;
  animation-delay: -0.2s;
}
.sk-circle .sk-circle12:before {
  -webkit-animation-delay: -0.1s;
  animation-delay: -0.1s;
}

@-webkit-keyframes sk-circleBounceDelay {
  0%,
  80%,
  100% {
    -webkit-transform: scale(0);
    transform: scale(0);
  }
  40% {
    -webkit-transform: scale(1);
    transform: scale(1);
  }
}

@keyframes sk-circleBounceDelay {
  0%,
  80%,
  100% {
    -webkit-transform: scale(0);
    transform: scale(0);
  }
  40% {
    -webkit-transform: scale(1);
    transform: scale(1);
  }
}
</style>
