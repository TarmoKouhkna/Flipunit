<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:html="http://www.w3.org/1999/xhtml"
                xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>XML Sitemap - Flipunit.eu</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <style type="text/css">
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #545454;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
          }
          h1 {
            color: #333;
            font-size: 24px;
            margin-bottom: 10px;
          }
          .intro {
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
          }
          .intro p {
            margin: 5px 0;
            font-size: 14px;
          }
          .intro a {
            color: #0066cc;
            text-decoration: none;
          }
          .intro a:hover {
            text-decoration: underline;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
          }
          th {
            background-color: #0066cc;
            color: #fff;
            text-align: left;
            padding: 12px;
            font-weight: 600;
            font-size: 14px;
          }
          td {
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
            font-size: 14px;
          }
          tr:hover {
            background-color: #f9f9f9;
          }
          tr:last-child td {
            border-bottom: none;
          }
          a {
            color: #0066cc;
            text-decoration: none;
            word-break: break-all;
          }
          a:hover {
            text-decoration: underline;
          }
          .count {
            color: #666;
            font-size: 13px;
            margin-bottom: 15px;
          }
        </style>
      </head>
      <body>
        <h1>XML Sitemap</h1>
        <div class="intro">
          <p>This is an XML Sitemap, generated for search engines like Google, Bing, and others.</p>
          <p>You can find more information about XML sitemaps at <a href="https://www.sitemaps.org" target="_blank">sitemaps.org</a>.</p>
        </div>
        <p class="count">
          <xsl:text>Found </xsl:text>
          <xsl:value-of select="count(sitemap:urlset/sitemap:url)"/>
          <xsl:text> URL(s) in this sitemap.</xsl:text>
        </p>
        <table>
          <tr>
            <th>#</th>
            <th>URL</th>
            <th>Last Modified</th>
            <th>Change Frequency</th>
            <th>Priority</th>
          </tr>
          <xsl:for-each select="sitemap:urlset/sitemap:url">
            <tr>
              <td>
                <xsl:value-of select="position()"/>
              </td>
              <td>
                <xsl:variable name="itemURL">
                  <xsl:value-of select="sitemap:loc"/>
                </xsl:variable>
                <a href="{$itemURL}">
                  <xsl:value-of select="sitemap:loc"/>
                </a>
              </td>
              <td>
                <xsl:value-of select="sitemap:lastmod"/>
              </td>
              <td>
                <xsl:value-of select="sitemap:changefreq"/>
              </td>
              <td>
                <xsl:value-of select="sitemap:priority"/>
              </td>
            </tr>
          </xsl:for-each>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>

