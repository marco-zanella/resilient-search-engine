FROM docker.elastic.co/elasticsearch/elasticsearch:8.18.0

# Install required plugins
RUN elasticsearch-plugin install --batch analysis-icu \
    && elasticsearch-plugin install --batch analysis-phonetic