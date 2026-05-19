from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Neo4jGraphStore:
    def __init__(self) -> None:
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE") or None
        self._driver = None

    @property
    def enabled(self) -> bool:
        return bool(self.uri and self.username and self.password)

    def _driver_or_none(self):
        if not self.enabled:
            return None
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "connected": False}
        try:
            with self._driver_or_none().session(database=self.database) as session:
                session.run("RETURN 1 AS ok").single()
            return {"enabled": True, "connected": True, "database": self.database}
        except Exception as exc:
            return {"enabled": True, "connected": False, "error": str(exc)}

    def sync_route_graph(
        self,
        run_id: int,
        user: dict[str, Any],
        profile: dict[str, Any],
        plan: dict[str, Any],
        graph: dict[str, Any],
    ) -> bool:
        driver = self._driver_or_none()
        if driver is None:
            return False

        with driver.session(database=self.database) as session:
            session.execute_write(
                self._write_route_graph,
                run_id,
                user,
                profile,
                plan,
                graph,
            )
        return True

    @staticmethod
    def _write_route_graph(tx, run_id: int, user: dict[str, Any], profile: dict[str, Any], plan: dict[str, Any], graph: dict[str, Any]) -> None:
        tx.run(
            """
            MERGE (u:User {id: $user_id})
            SET u.full_name = $full_name,
                u.email = $email,
                u.zip_code = $zip_code,
                u.language = $language,
                u.transport_mode = $transport_mode,
                u.insurance_status = $insurance_status
            MERGE (r:RouteRun {id: $run_id})
            SET r.summary = $summary,
                r.created_at = datetime(),
                r.language = $language,
                r.urgency = $urgency
            MERGE (u)-[:HAS_ROUTE_RUN]->(r)
            """,
            user_id=int(user["id"]),
            full_name=user["full_name"],
            email=user["email"],
            zip_code=profile["zip_code"],
            language=profile["language"],
            transport_mode=profile["transport_mode"],
            insurance_status=profile["insurance_status"],
            run_id=run_id,
            summary=plan["summary"],
            urgency=profile["urgency"],
        )

        for node in graph.get("nodes", []):
            props = {
                "entity_id": node["id"],
                "label": node["label"],
                "kind": node["type"],
                "score": node.get("score"),
                "detail": node.get("detail"),
                "latitude": node.get("latitude"),
                "longitude": node.get("longitude"),
            }
            tx.run(
                """
                MERGE (n:CareEntity {entity_id: $entity_id})
                SET n.label = $label,
                    n.kind = $kind,
                    n.score = $score,
                    n.detail = $detail,
                    n.latitude = $latitude,
                    n.longitude = $longitude
                WITH n
                MATCH (r:RouteRun {id: $run_id})
                MERGE (r)-[:INCLUDES]->(n)
                """,
                run_id=run_id,
                **props,
            )

        for edge in graph.get("edges", []):
            tx.run(
                """
                MATCH (source:CareEntity {entity_id: $source_id})
                MATCH (target:CareEntity {entity_id: $target_id})
                MERGE (source)-[rel:CARE_LINK {run_id: $run_id, source_id: $source_id, target_id: $target_id, label: $label}]->(target)
                SET rel.weight = $weight
                """,
                run_id=run_id,
                source_id=edge["source"],
                target_id=edge["target"],
                label=edge["label"],
                weight=edge.get("weight"),
            )

    def fetch_route_graph(self, run_id: int) -> Optional[dict[str, Any]]:
        driver = self._driver_or_none()
        if driver is None:
            return None

        with driver.session(database=self.database) as session:
            record = session.execute_read(self._read_route_graph, run_id)
        return record

    @staticmethod
    def _read_route_graph(tx, run_id: int) -> Optional[dict[str, Any]]:
        nodes_result = tx.run(
            """
            MATCH (:RouteRun {id: $run_id})-[:INCLUDES]->(n:CareEntity)
            RETURN n.entity_id AS id,
                   n.label AS label,
                   n.kind AS type,
                   n.score AS score,
                   n.detail AS detail,
                   n.latitude AS latitude,
                   n.longitude AS longitude
            ORDER BY n.kind, n.label
            """,
            run_id=run_id,
        )
        edges_result = tx.run(
            """
            MATCH (source:CareEntity)-[rel:CARE_LINK {run_id: $run_id}]->(target:CareEntity)
            RETURN source.entity_id AS source,
                   target.entity_id AS target,
                   rel.label AS label,
                   rel.weight AS weight
            ORDER BY rel.label
            """,
            run_id=run_id,
        )

        nodes = [record.data() for record in nodes_result]
        edges = [record.data() for record in edges_result]
        if not nodes and not edges:
            return None
        return {"nodes": nodes, "edges": edges}


graph_store = Neo4jGraphStore()
