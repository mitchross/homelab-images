FROM vllm/vllm-openai:v0.33.0@sha256:d825baf9ce4b1b6bfc5ecc7b79880c7e6748c65a72d697ce3d47607aafa84c6e
COPY patches/ /etc/club3090/
COPY SOURCE_REF /etc/club3090/SOURCE_REF
COPY smoke.py /opt/dualfast/smoke.py
RUN _eb="$(python3 /etc/club3090/effort_budget.py shell-env --engine vllm --default-effort medium --low 4096 --medium 16384 --xhigh 32768)" \
    && eval "$_eb" \
    && bash /etc/club3090/effort-budget/install.sh \
    && bash /etc/club3090/default-thinking-budget/install.sh \
    && VLLM_MARLIN_INPUT_DTYPE=int8 bash /etc/club3090/w4a8/install.sh \
    && bash /etc/club3090/pr48375/install.sh \
    && FI_PINQ_LIB_ALL=0 FI_PINQ_LIB_ROOT="$(python3 -c 'import importlib.util,pathlib; print(pathlib.Path(importlib.util.find_spec("flashinfer").origin).parent)')" \
       bash /etc/club3090/flashinfer-decode-pin/install.sh \
    && python3 /opt/dualfast/smoke.py
LABEL org.opencontainers.image.source="https://github.com/mitchross/homelab-images" \
      org.opencontainers.image.url="https://github.com/noonghunna/club-3090" \
      org.opencontainers.image.revision="def9711c8e6dc8bb3e6d1ecaad795b3bbb4bb665"
