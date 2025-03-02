# ERBehInjector

Make sure to use both files.

Each animation entry (a215_030000, for example), is connected to a behaviour in the ‘behbnd.dcx’ file. This registers the entry so it can properly be used in-game. The registry also determines the callable name of the entry (eventName), which can be used in the HKS file. For example, all ‘030000’ (right-hand 1st R1) entries have been assigned the name ‘AttackRightLight1’ in their registry, which can be called through the HKS. 

With this tool, you’ll be able to add a new animation entry under any unused/open ID and hook it to a unique name, then call it with the HKS.

Credits to: https://docs.google.com/document/d/1YFIyfn1AQyQi81fv0Mjzh0YjcLnJMbnTOhLmLmQGhpE/edit?fbclid=IwZXh0bgNhZW0CMTEAAR3tN8EP0V3BjvADplsJiUR8zhAaYE0XK3-tLIsEv1wHxYrjs82_c6GxSKw_aem_k0e0ZwfCd_uf3Z_yOI6A6A&tab=t.0
