import pykube

from atmosphere import logger
from atmosphere.tasks import kubernetes

LOG = logger.get_logger()


class HelmRepository(pykube.objects.NamespacedAPIObject):
    version = "source.toolkit.fluxcd.io/v1beta2"
    endpoint = "helmrepositories"
    kind = "HelmRepository"


class CreateOrUpdateHelmRepositoryTask(kubernetes.CreateOrUpdateKubernetesObjectTask):
    def __init__(self, namespace: str, name: str, url: str, *args, **kwargs):
        super().__init__(
            HelmRepository,
            namespace,
            name,
            requires=set(["namespace", "name", "url"]),
            inject={"name": name, "url": url},
            *args,
            **kwargs,
        )

    def generate_object(
        self, namespace: pykube.Namespace, name: str, url: str, *args, **kwargs
    ):
        return HelmRepository(
            self.api,
            {
                "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                "kind": "HelmRepository",
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                },
                "spec": {
                    "interval": "1m",
                    "url": url,
                },
            },
        )

    def update_object(
        self, resource: pykube.objects.APIObject, url: str, *args, **kwargs
    ):
        resource.obj["spec"]["url"] = url


class HelmRelease(pykube.objects.NamespacedAPIObject):
    version = "helm.toolkit.fluxcd.io/v2beta1"
    endpoint = "helmreleases"
    kind = "HelmRelease"


class CreateOrUpdateHelmReleaseTask(kubernetes.CreateOrUpdateKubernetesObjectTask):
    def __init__(
        self,
        namespace: str,
        name: str,
        repository: str,
        chart: str,
        version: str,
        values: dict = {},
        values_from: list = [],
        *args,
        **kwargs,
    ):
        kwargs.setdefault("requires", set())
        kwargs["requires"] = kwargs["requires"].union(
            set(
                [
                    "namespace",
                    "name",
                    "repository",
                    "chart",
                    "version",
                    "values",
                    "values_from",
                ]
            )
        )

        super().__init__(
            HelmRelease,
            namespace,
            name,
            rebind={"repository": f"helm-repository-{namespace}-{repository}"},
            inject={
                "name": name,
                "repository": repository,
                "chart": chart,
                "version": version,
                "values": values,
                "values_from": values_from,
            },
            *args,
            **kwargs,
        )

    def generate_object(
        self,
        namespace: pykube.Namespace,
        name: str,
        repository: HelmRepository,
        chart: str,
        version: str,
        values: dict,
        values_from: list,
        *args,
        **kwargs,
    ) -> HelmRelease:
        return HelmRelease(
            self.api,
            {
                "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                "kind": "HelmRelease",
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
                },
                "spec": {
                    "interval": "60s",
                    "chart": {
                        "spec": {
                            "chart": chart,
                            "version": version,
                            "sourceRef": {
                                "kind": "HelmRepository",
                                "name": repository.name,
                            },
                        }
                    },
                    "install": {
                        "disableWait": True,
                    },
                    "upgrade": {
                        "disableWait": True,
                    },
                    "values": values,
                    "valuesFrom": values_from,
                },
            },
        )

    def update_object(
        self,
        resource: HelmRelease,
        values: dict = {},
        values_from: list = [],
        *args,
        **kwargs,
    ):
        resource.obj["spec"]["values"] = values
        resource.obj["spec"]["valuesFrom"] = values_from
