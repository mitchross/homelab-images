FROM vllm/vllm-openai:v0.32.0@sha256:befccf0e7e4089aa23926bb6f887a85c0d46c2a99e6de5c5ffdf5cb7957c5b34
COPY patches/ /etc/club3090/
COPY SOURCE_REF /etc/club3090/SOURCE_REF
COPY smoke.py /opt/dualfast/smoke.py
RUN VLLM_MARLIN_INPUT_DTYPE=int8 bash /etc/club3090/w4a8/install.sh \
    && bash /etc/club3090/pr48375/install.sh \
    && FI_PINQ_LIB_ALL=0 FI_PINQ_LIB_ROOT="$(python3 -c 'import importlib.util,pathlib; print(pathlib.Path(importlib.util.find_spec("flashinfer").origin).parent)')" \
       bash /etc/club3090/flashinfer-decode-pin/install.sh \
    && python3 /opt/dualfast/smoke.py
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.url="https://github.com/noonghunna/club-3090" \
      org.opencontainers.image.revision="def9711c8e6dc8bb3e6d1ecaad795b3bbb4bb665"
