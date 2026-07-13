/*
 * 雙音符電商平台 SDK (DragonCommerce SDK)
 * 合作方前端嵌入此檔，顧客下單即自動回報中央統計中心。
 * 數據所有權歸龍族（dragon-clan），客戶前端只是展示層。
 *
 * 使用方式（店前端 index.html 引入）：
 *   <script src="https://<STATS_HOST>/sdk.js"></script>
 *   <script>
 *     DragonCommerce.init({ storeId: 'exosome', apiKey: 'dc_exo_xxx' });
 *     // 顧客點購買：
 *     DragonCommerce.trackSale('1', 1, 'qrcode');
 *   </script>
 */
(function (global) {
  const DEFAULT_HOST = "https://italiano-www-parish-pcs.trycloudflare.com"; // 固定網址（Cloudflare Tunnel，重啟會變更）
  let config = { storeId: "", apiKey: "", host: DEFAULT_HOST };

  const DragonCommerce = {
    init(opts) {
      config = Object.assign(config, opts);
      if (!config.storeId || !config.apiKey) {
        console.warn("[DragonCommerce] 缺少 storeId 或 apiKey");
      }
    },

    setHost(host) {
      config.host = host;
    },

    /**
     * 回報一筆成交。
     * @param {string} productId 商品 ID
     * @param {number} qty 數量
     * @param {string} method 付款方式: qrcode|linepay|cod|manual
     * @returns {Promise}
     */
    async trackSale(productId, qty = 1, method = "unknown") {
      const url = `${config.host}/track/sale`;
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            store: config.storeId,
            id: productId,
            qty: qty,
            method: method,
            api_key: config.apiKey,
          }),
        });
        if (!resp.ok) {
          console.warn("[DragonCommerce] 回報失敗:", resp.status);
        }
        return resp.json();
      } catch (e) {
        console.warn("[DragonCommerce] 網路錯誤（不影響顧客結帳）:", e);
        return null;
      }
    },
  };

  global.DragonCommerce = DragonCommerce;
})(window);
