# TTDS-RawData

## This README assumes that the ~78GB `enwiki-20211101-pages-articles-multistream.xml` resides within this directory.

### You can download a 1237KB vesion of `enwiki-20211101-pages-articles-multistream.xml` which contains the first 6000 lines and the last 8000 lines of the original XML (with trailing tags removed for XML validity). The XML (_Salami Slice_ XSD design) schema is as follows:

```xml
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://www.mediawiki.org/xml/export-0.10/" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="namespace">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute type="xs:short" name="key" use="optional"/>
          <xs:attribute type="xs:string" name="case" use="optional"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="sitename" type="xs:string"/>
  <xs:element name="dbname" type="xs:string"/>
  <xs:element name="base" type="xs:string"/>
  <xs:element name="generator" type="xs:string"/>
  <xs:element name="case" type="xs:string"/>
  <xs:element name="namespaces">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:namespace" maxOccurs="unbounded" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="username" type="xs:string"/>
  <xs:element name="id" type="xs:int"/>
  <xs:element name="parentid" type="xs:int"/>
  <xs:element name="timestamp" type="xs:dateTime"/>
  <xs:element name="contributor">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:username" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:id" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:ip" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="minor" type="xs:string"/>
  <xs:element name="comment" type="xs:string"/>
  <xs:element name="model" type="xs:string"/>
  <xs:element name="format" type="xs:string"/>
  <xs:element name="text">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute type="xs:int" name="bytes" use="optional"/>
          <xs:attribute ref="xml:space"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="sha1" type="xs:string"/>
  <xs:element name="title" type="xs:string"/>
  <xs:element name="ns" type="xs:short"/>
  <xs:element name="redirect">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute type="xs:string" name="title" use="optional"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>
  <xs:element name="revision">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:id" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:parentid" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:timestamp" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:contributor" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:minor" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:comment" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:model" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:format" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:text" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:sha1" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="ip" type="xs:string"/>
  <xs:element name="siteinfo">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:sitename" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:dbname" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:base" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:generator" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:case" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:namespaces" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="page">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:title" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:ns" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:id" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:redirect" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:revision" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="mediawiki">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="exp:siteinfo" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
        <xs:element ref="exp:page" maxOccurs="unbounded" minOccurs="0" xmlns:exp="http://www.mediawiki.org/xml/export-0.10/"/>
      </xs:sequence>
      <xs:attribute type="xs:float" name="version"/>
      <xs:attribute ref="xml:lang"/>
    </xs:complexType>
  </xs:element>
</xs:schema>
```